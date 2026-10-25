from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    ToolMessage,
)

import agent.nodes as agent_nodes_module
import api.routes.chat as chat_route
from schemas.chat import ChatRequest


class FakeRepository:
    def __init__(self, _db):
        self.session = SimpleNamespace(id=12, title="Question")
        self.saved_messages = []

    async def create_session(self, _user_id, _title):
        return self.session

    async def get_session(self, session_id, _user_id):
        if session_id == self.session.id:
            return self.session
        return None

    async def get_messages(self, _session_id):
        return []

    async def add_messages(self, _session, messages):
        self.saved_messages.extend(messages)


def make_user(user_id):
    return SimpleNamespace(id=user_id, user_roles=[])


class FakeMCPClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def initialize(self):
        return None

    async def list_tools(self):
        return SimpleNamespace(tools=[])


class FakeAgent:
    def __init__(self, disconnect=False, fail=False):
        self.disconnect = disconnect
        self.fail = fail

    async def astream(self, *_args, **_kwargs):
        if self.fail:
            raise RuntimeError("simulated model failure")

        yield "messages", (
            AIMessageChunk(content="Hello "),
            {"langgraph_node": "agent"},
        )

        if self.disconnect:
            return

        yield "updates", {
            "agent": {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "get_my_leave_balance",
                                "args": {},
                                "id": "call-1",
                                "type": "tool_call",
                            }
                        ],
                    )
                ]
            }
        }
        yield "updates", {
            "tools": {
                "messages": [
                    ToolMessage(
                        content="7 days",
                        tool_call_id="call-1",
                        name="get_my_leave_balance",
                    )
                ]
            }
        }
        yield "messages", (
            AIMessageChunk(content="You have 7 days."),
            {"langgraph_node": "agent"},
        )
        yield "updates", {
            "agent": {"messages": [AIMessage(content="You have 7 days.")]}
        }


class FakeRequest:
    def __init__(self, disconnected=False):
        self.disconnected = disconnected

    async def is_disconnected(self):
        return self.disconnected


async def read_sse_body(response):
    chunks = []
    async for chunk in response.body_iterator:
        if isinstance(chunk, bytes):
            chunks.append(chunk)
        else:
            chunks.append(chunk.encode())
    return b"".join(chunks).decode()


def install_fake_services(monkeypatch, disconnect=False, fail=False):
    repository = FakeRepository(None)
    request_headers = {}

    @asynccontextmanager
    async def fake_streamable_http_client(_url, http_client):
        request_headers.update(http_client.headers)
        yield object(), object(), lambda: None

    monkeypatch.setattr(
        chat_route,
        "ChatRepository",
        lambda _db: repository,
    )
    monkeypatch.setattr(
        chat_route,
        "streamable_http_client",
        fake_streamable_http_client,
    )
    monkeypatch.setattr(
        chat_route,
        "ClientSession",
        lambda _read, _write: FakeMCPClientSession(),
    )
    monkeypatch.setattr(
        chat_route,
        "create_agent",
        lambda **_kwargs: FakeAgent(disconnect=disconnect, fail=fail),
    )

    return repository, request_headers


@pytest.mark.asyncio
async def test_stream_sends_events_and_saves_completed_turn(monkeypatch):
    repository, request_headers = install_fake_services(monkeypatch)

    response = await chat_route.send_message_stream(
        request=ChatRequest(message="Check my balance"),
        http_request=FakeRequest(),
        credentials=HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token",
        ),
        current_user=make_user(4),
        db=object(),
    )
    body = await read_sse_body(response)

    assert response.media_type == "text/event-stream"
    assert "event: status" in body
    assert '"status": "thinking"' in body
    assert "event: content" in body
    assert "event: tool_status" in body
    assert '"status": "started"' in body
    assert '"status": "completed"' in body
    assert "event: complete" in body
    assert '"session_id": 12' in body
    assert request_headers["authorization"] == "Bearer test-token"
    assert [message.type for message in repository.saved_messages] == [
        "ai",
        "tool",
        "ai",
    ]


@pytest.mark.asyncio
async def test_stream_does_not_save_an_incomplete_turn_after_disconnect(monkeypatch):
    repository, _ = install_fake_services(monkeypatch, disconnect=True)

    response = await chat_route.send_message_stream(
        request=ChatRequest(message="Check my balance"),
        http_request=FakeRequest(disconnected=True),
        credentials=HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token",
        ),
        current_user=make_user(4),
        db=object(),
    )
    body = await read_sse_body(response)

    assert "event: complete" not in body
    assert repository.saved_messages == []


@pytest.mark.asyncio
async def test_stream_sends_error_event_when_agent_fails(monkeypatch):
    repository, _ = install_fake_services(monkeypatch, fail=True)

    response = await chat_route.send_message_stream(
        request=ChatRequest(message="Check my balance"),
        http_request=FakeRequest(),
        credentials=HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token",
        ),
        current_user=make_user(4),
        db=object(),
    )
    body = await read_sse_body(response)

    assert "event: error" in body
    assert chat_route.CHAT_FAILURE_MESSAGE in body
    assert "event: complete" not in body
    assert repository.saved_messages == []


@pytest.mark.asyncio
async def test_chat_returns_helpful_error_when_agent_fails(monkeypatch):
    install_fake_services(monkeypatch, fail=True)

    with pytest.raises(HTTPException) as error:
        await chat_route.send_message(
            request=ChatRequest(message="Check my balance"),
            credentials=HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="test-token",
            ),
            current_user=make_user(4),
            db=object(),
        )

    assert error.value.status_code == 502
    assert error.value.detail == chat_route.CHAT_FAILURE_MESSAGE
    assert "simulated model failure" not in error.value.detail


@pytest.mark.parametrize(
    ("error", "expected_message"),
    [
        (
            TimeoutError(),
            "The chat request timed out while waiting for a service.",
        ),
        (
            httpx.ConnectError("connection refused"),
            "Could not connect to a chat service.",
        ),
        (
            httpx.HTTPStatusError(
                "unauthorized",
                request=httpx.Request("POST", "https://example.test"),
                response=httpx.Response(
                    401,
                    request=httpx.Request("POST", "https://example.test"),
                ),
            ),
            "A connected service rejected its credentials.",
        ),
    ],
)
def test_chat_error_message_explains_known_failures_without_details(
    error,
    expected_message,
):
    message = chat_route._chat_error_message(error)

    assert expected_message in message
    assert not str(error) or str(error) not in message


@pytest.mark.asyncio
async def test_stream_rejects_a_session_owned_by_another_user(monkeypatch):
    install_fake_services(monkeypatch)

    with pytest.raises(HTTPException) as error:
        await chat_route.send_message_stream(
            request=ChatRequest(message="Continue", session_id=99),
            http_request=FakeRequest(),
            credentials=HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="test-token",
            ),
            current_user=make_user(4),
            db=object(),
        )

    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_agent_combines_streamed_text_and_tool_call_chunks(monkeypatch):
    class FakeLLM:
        def bind_tools(self, _tools):
            return self

        async def astream(self, _messages):
            yield AIMessageChunk(content="Checking ")
            yield AIMessageChunk(content="your balance.")
            yield AIMessageChunk(
                content="",
                tool_call_chunks=[
                    {
                        "name": "get_my_leave_balance",
                        "args": "{}",
                        "id": "call-99",
                        "index": 0,
                    }
                ],
            )

    monkeypatch.setattr(agent_nodes_module, "get_llm", lambda: FakeLLM())
    nodes = agent_nodes_module.AgentNodes(mcp_session=object(), mcp_tools=[])

    result = await nodes.agent_node(
        {"messages": [HumanMessage(content="How many leave days?")]}
    )
    assistant_message = result["messages"][0]

    assert isinstance(assistant_message, AIMessage)
    assert assistant_message.content == "Checking your balance."
    assert assistant_message.tool_calls[0]["name"] == "get_my_leave_balance"
