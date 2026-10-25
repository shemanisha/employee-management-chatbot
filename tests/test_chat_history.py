from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import pytest

from repositories.chat_repository import ChatRepository
from services.chat_service import get_recent_messages, message_to_response


class FakeScalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return FakeScalars(self.rows)


class FakeDatabase:
    def __init__(self):
        self.rows = []

    def add(self, row):
        self.rows.append(row)

    async def commit(self):
        pass

    async def execute(self, query):
        return FakeResult(self.rows)


def test_history_keeps_the_latest_ten_complete_turns():
    messages = []

    for turn_number in range(12):
        tool_call_id = f"call-{turn_number}"
        messages.extend(
            [
                HumanMessage(content=f"Question {turn_number}"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "get_my_leave_balance",
                            "args": {},
                            "id": tool_call_id,
                            "type": "tool_call",
                        }
                    ],
                ),
                ToolMessage(
                    content="Balance result",
                    tool_call_id=tool_call_id,
                    name="get_my_leave_balance",
                ),
                AIMessage(content="Here is your balance."),
            ]
        )

    recent_messages = get_recent_messages(messages)

    assert len(recent_messages) == 40
    assert recent_messages[0].content == "Question 2"
    assert recent_messages[1].tool_calls[0]["id"] == "call-2"
    assert recent_messages[2].tool_call_id == "call-2"


def test_tool_message_response_keeps_tool_call_details():
    message = ToolMessage(
        content="7 days remaining",
        tool_call_id="call-123",
        name="get_my_leave_balance",
    )

    response = message_to_response(message)

    assert response["role"] == "tool"
    assert response["content"] == "7 days remaining"
    assert response["tool_call_id"] == "call-123"
    assert response["tool_name"] == "get_my_leave_balance"


@pytest.mark.asyncio
async def test_repository_restores_tool_calls_from_saved_messages():
    database = FakeDatabase()
    repository = ChatRepository(database)
    chat_session = SimpleNamespace(id=5, updated_at=None)
    messages = [
        HumanMessage(content="Check my leave balance"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_my_leave_balance",
                    "args": {},
                    "id": "call-456",
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(
            content="7 days remaining",
            tool_call_id="call-456",
            name="get_my_leave_balance",
        ),
    ]

    await repository.add_messages(chat_session, messages)

    assert all(
        set(row.__dict__).isdisjoint(
            {"tool_calls", "tool_call_id", "status"}
        )
        for row in database.rows
    )

    restored_messages = await repository.get_messages(chat_session.id)

    assert len(restored_messages) == 3
    assert restored_messages[1].tool_calls[0]["id"] == "call-456"
    assert restored_messages[2].tool_call_id == "call-456"
