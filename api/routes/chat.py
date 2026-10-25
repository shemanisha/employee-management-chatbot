import asyncio
import json
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import create_agent
from api.dependencies import bearer_scheme, get_current_user
from core.permissions import get_user_roles
from core.config import settings
from db.session import get_db
from repositories.chat_repository import ChatRepository
from schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
)
from services.chat_service import (
    MAX_REPLY_CHARACTERS,
    filter_tools_for_user,
    get_recent_messages,
    message_to_response,
    sanitize_assistant_reply,
)
from core.permissions import get_user_roles


logger = logging.getLogger(__name__)

CHAT_FAILURE_MESSAGE = (
    "The chat service encountered an unexpected error. Please try again. "
    "If it continues, check the server logs."
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

def _sse_event(event_name: str, event_data: dict) -> str:
    """Format one Server-Sent Event for the browser."""
    data = json.dumps(event_data, ensure_ascii=False)
    return f"event: {event_name}\ndata: {data}\n\n"


def _text_from_chunk(chunk: AIMessageChunk) -> str:
    """Get readable text from a model chunk."""
    if isinstance(chunk.content, str):
        return chunk.content

    text_parts = []
    for content_part in chunk.content:
        if isinstance(content_part, dict) and content_part.get("type") == "text":
            text_parts.append(content_part.get("text", ""))

    return "".join(text_parts)


def _chat_error_message(error: Exception) -> str:
    """Return actionable guidance without exposing internal exception details."""
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return (
            "The chat request timed out while waiting for a service. "
            "Check that Ollama and the MCP server are responsive, then try again."
        )

    if isinstance(error, httpx.ConnectError):
        return (
            "Could not connect to a chat service. Check that Ollama and the MCP "
            "server are running and their configured URLs are correct."
        )

    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        if status_code in (401, 403):
            return (
                "A connected service rejected its credentials. Check the "
                "service authentication configuration."
            )
        if status_code == 404:
            return (
                "A configured chat endpoint or model was not found. Check the "
                "MCP server URL and Ollama model name."
            )
        return (
            "A connected service returned an error. Check the Ollama and MCP "
            "server logs, then try again."
        )

    if isinstance(error, SQLAlchemyError):
        return (
            "Could not access or save your conversation history. Check the "
            "database connection, then try again."
        )

    if isinstance(error, ValueError):
        return (
            "The assistant returned an invalid response. Please try your "
            "request again."
        )

    return CHAT_FAILURE_MESSAGE


@asynccontextmanager
async def _connect_to_mcp(access_token: str):
    """Open an authenticated MCP session and discover its tools."""
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(60, connect=20),
    ) as http_client:
        async with streamable_http_client(
            settings.MCP_SERVER_URL,
            http_client=http_client,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                async with asyncio.timeout(20):
                    await mcp_session.initialize()
                    tools_response = await mcp_session.list_tools()

                yield mcp_session, tools_response.tools


async def _get_or_create_session(repository, user_id: int, request: ChatRequest):
    """Create a conversation or find one owned by the signed-in user."""
    if request.session_id is None:
        return await repository.create_session(user_id, request.message)

    return await repository.get_session(request.session_id, user_id)


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or continue a conversation and return the assistant's reply."""
    repository = ChatRepository(db)

    chat_session = await _get_or_create_session(
        repository,
        current_user.id,
        request,
    )
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        saved_messages = await repository.get_messages(chat_session.id)
        context_messages = get_recent_messages(saved_messages)
        starting_message_count = len(context_messages)
        context_messages.append(HumanMessage(content=request.message))

        # Forward this user's token so MCP applies its normal role checks.
        async with _connect_to_mcp(credentials.credentials) as (
            mcp_session,
            discovered_tools,
        ):
            mcp_tools = filter_tools_for_user(
                discovered_tools,
                set(get_user_roles(current_user)),
            )
            agent = create_agent(
                mcp_session=mcp_session,
                mcp_tools=mcp_tools,
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
        reply = sanitize_assistant_reply(
            all_messages[-1].content,
            {tool.name for tool in mcp_tools},
        )
        new_messages[-1] = new_messages[-1].model_copy(
            update={"content": reply}
        )
        await repository.add_messages(chat_session, new_messages)

        return ChatResponse(
            session_id=chat_session.id,
            reply=reply,
        )

    except Exception as error:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502,
            detail=_chat_error_message(error),
        ) from error


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream status and answer events while the agent handles a message."""
    repository = ChatRepository(db)
    chat_session = await _get_or_create_session(
        repository,
        current_user.id,
        request,
    )
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    async def generate_events():
        try:
            yield _sse_event(
                "status",
                {"status": "starting", "session_id": chat_session.id},
            )

            saved_messages = await repository.get_messages(chat_session.id)
            context_messages = get_recent_messages(saved_messages)
            context_messages.append(HumanMessage(content=request.message))
            new_messages = []

            yield _sse_event("status", {"status": "connecting"})
            async with _connect_to_mcp(credentials.credentials) as (
                mcp_session,
                discovered_tools,
            ):
                mcp_tools = filter_tools_for_user(
                    discovered_tools,
                    set(get_user_roles(current_user)),
                )
                yield _sse_event("status", {"status": "thinking"})

                agent = create_agent(
                    mcp_session=mcp_session,
                    mcp_tools=mcp_tools,
                )

                streamed_reply_length = 0
                async for mode, data in agent.astream(
                    {"messages": context_messages},
                    config={"recursion_limit": 12},
                    stream_mode=["messages", "updates"],
                ):
                    if await http_request.is_disconnected():
                        logger.info(
                            "Client disconnected during chat session %s",
                            chat_session.id,
                        )
                        return

                    if mode == "messages":
                        message_chunk, metadata = data
                        if (
                            metadata.get("langgraph_node") == "agent"
                            and isinstance(message_chunk, AIMessageChunk)
                        ):
                            text = _text_from_chunk(message_chunk)
                            if text:
                                streamed_reply_length += len(text)
                                if streamed_reply_length > MAX_REPLY_CHARACTERS:
                                    yield _sse_event(
                                        "error",
                                        {"message": "Assistant response is too long"},
                                    )
                                    return

                    elif mode == "updates":
                        for node_name, update in data.items():
                            node_messages = update.get("messages", [])
                            new_messages.extend(node_messages)

                            if node_name == "agent":
                                for message in node_messages:
                                    if isinstance(message, AIMessage):
                                        for tool_call in message.tool_calls:
                                            yield _sse_event(
                                                "tool_status",
                                                {
                                                    "tool": "Employee management action",
                                                    "status": "started",
                                                },
                                            )

                            elif node_name == "tools":
                                for message in node_messages:
                                    if isinstance(message, ToolMessage):
                                        yield _sse_event(
                                            "tool_status",
                                            {
                                                "tool": "Employee management action",
                                                "status": (
                                                    "error"
                                                    if message.status == "error"
                                                    else "completed"
                                                ),
                                            },
                                        )


            if (
                not new_messages
                or not isinstance(new_messages[-1], AIMessage)
                or new_messages[-1].tool_calls
            ):
                raise RuntimeError("The agent did not return a final answer")

            yield _sse_event("status", {"status": "saving"})
            reply = sanitize_assistant_reply(
                new_messages[-1].content,
                {tool.name for tool in mcp_tools},
            )
            new_messages[-1] = new_messages[-1].model_copy(
                update={"content": reply}
            )
            await repository.add_messages(chat_session, new_messages)

            yield _sse_event("content", {"content": reply})
            yield _sse_event(
                "complete",
                {
                    "session_id": chat_session.id,
                    "reply": reply,
                },
            )

        except asyncio.CancelledError:
            logger.info(
                "Streaming chat session %s was cancelled",
                chat_session.id,
            )
            raise
        except Exception as error:
            logger.exception("Streaming chat request failed")
            yield _sse_event(
                "error",
                {"message": _chat_error_message(error)},
            )

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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
