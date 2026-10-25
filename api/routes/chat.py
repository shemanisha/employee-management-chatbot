import asyncio
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from langchain_core.messages import AIMessage, HumanMessage
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.exceptions import McpError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import create_agent
from api.dependencies import bearer_scheme, get_current_user
from core.config import settings
from db.session import get_db
from repositories.chat_repository import ChatRepository
from schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
)
from services.chat_service import get_recent_messages, message_to_response


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or continue a conversation and return the assistant's reply."""
    repository = ChatRepository(db)

    if request.session_id is None:
        chat_session = await repository.create_session(
            user_id=current_user.id,
            title=request.message,
        )
    else:
        chat_session = await repository.get_session(
            request.session_id,
            current_user.id,
        )
        if chat_session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found",
            )

    try:
        saved_messages = await repository.get_messages(chat_session.id)
        context_messages = get_recent_messages(saved_messages)
        starting_message_count = len(context_messages)
        context_messages.append(HumanMessage(content=request.message))

        # Forward this user's token so the MCP server applies its normal
        # authentication and role checks to every tool call.
        headers = {
            "Authorization": f"Bearer {credentials.credentials}",
        }

        async with streamablehttp_client(
            settings.MCP_SERVER_URL,
            headers=headers,
            timeout=20,
            sse_read_timeout=60,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                async with asyncio.timeout(20):
                    await mcp_session.initialize()
                    tools_response = await mcp_session.list_tools()

                agent = create_agent(
                    mcp_session=mcp_session,
                    mcp_tools=tools_response.tools,
                )
                result = await agent.ainvoke(
                    {"messages": context_messages},
                    config={"recursion_limit": 12},
                )

        all_messages = result["messages"]
        if (
            not all_messages
            or not isinstance(all_messages[-1], AIMessage)
            or all_messages[-1].tool_calls
        ):
            raise RuntimeError("The agent did not return a final answer")

        # Save only this request's new messages, not the older context again.
        new_messages = all_messages[starting_message_count:]
        await repository.add_messages(chat_session, new_messages)

        return ChatResponse(
            session_id=chat_session.id,
            reply=str(all_messages[-1].content),
        )

    except Exception as error:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502,
            detail="The chat service could not complete your request",
        ) from error


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_chat_sessions(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List only the signed-in user's conversations."""
    return await ChatRepository(db).get_user_sessions(current_user.id)


@router.get(
    "/sessions/{session_id}",
    response_model=list[ChatMessageResponse],
)
async def get_chat_history(
    session_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Read a conversation only when it belongs to the signed-in user."""
    repository = ChatRepository(db)
    chat_session = await repository.get_session(session_id, current_user.id)

    if chat_session is None:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found",
        )

    messages = await repository.get_messages(chat_session.id)
    return [message_to_response(message) for message in messages]
