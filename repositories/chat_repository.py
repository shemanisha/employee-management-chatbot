from datetime import datetime, timezone
import json

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from sqlalchemy import select

from models.chat_message import ChatMessage
from models.chat_session import ChatSession


TOOL_MESSAGE_PREFIX = "__CHAT_TOOL_DATA__:"


class ChatRepository:
    """Read and save chat sessions and their messages."""

    def __init__(self, db):
        self.db = db

    async def create_session(
        self,
        user_id: int,
        title: str,
    ) -> ChatSession:
        """Create a conversation for the signed-in user."""
        chat_session = ChatSession(
            user_id=user_id,
            title=title[:100],
        )
        self.db.add(chat_session)
        await self.db.commit()
        await self.db.refresh(chat_session)
        return chat_session

    async def get_session(
        self,
        session_id: int,
        user_id: int,
    ) -> ChatSession | None:
        """Return the session only when it belongs to this user."""
        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_sessions(self, user_id: int) -> list[ChatSession]:
        """List a user's sessions, most recently active first."""
        query = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_messages(self, session_id: int) -> list[BaseMessage]:
        """Load messages in the order they were saved."""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id)
        )
        result = await self.db.execute(query)
        saved_messages = result.scalars().all()

        # Rebuild the LangChain objects from the simple database columns.
        messages = []
        for saved_message in saved_messages:
            content = saved_message.content
            tool_data = None

            if content.startswith(TOOL_MESSAGE_PREFIX):
                tool_data = json.loads(content[len(TOOL_MESSAGE_PREFIX):])
                content = tool_data["content"]

            if saved_message.role == "human":
                message = HumanMessage(content=content)
            elif saved_message.role == "ai":
                message = AIMessage(
                    content=content,
                    tool_calls=(
                        tool_data.get("tool_calls", [])
                        if tool_data is not None
                        else []
                    ),
                )
            elif saved_message.role == "tool":
                if tool_data is None:
                    raise ValueError(
                        "Saved tool message is missing its call details"
                    )

                message = ToolMessage(
                    content=content,
                    tool_call_id=tool_data["tool_call_id"],
                    name=saved_message.tool_name,
                    status=tool_data.get("status", "success"),
                )
            else:
                raise ValueError(
                    f"Cannot restore unsupported chat message role: "
                    f"{saved_message.role}"
                )

            messages.append(message)

        return messages

    async def add_messages(
        self,
        chat_session: ChatSession,
        messages: list[BaseMessage],
    ) -> None:
        """Save the conversation messages and update its activity time."""
        for message in messages:
            tool_name = None
            content = message.content

            if isinstance(message, AIMessage):
                if message.tool_calls:
                    content = TOOL_MESSAGE_PREFIX + json.dumps({
                        "content": message.content,
                        "tool_calls": message.tool_calls,
                    })
            elif isinstance(message, ToolMessage):
                tool_name = message.name
                content = TOOL_MESSAGE_PREFIX + json.dumps({
                    "content": message.content,
                    "tool_call_id": message.tool_call_id,
                    "status": message.status,
                })

            if not isinstance(content, str):
                raise ValueError("Only text chat messages can be saved")

            self.db.add(
                ChatMessage(
                    session_id=chat_session.id,
                    role=message.type,
                    content=content,
                    tool_name=tool_name,
                )
            )

        chat_session.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
