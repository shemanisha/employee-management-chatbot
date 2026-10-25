from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from langchain_core.messages import AIMessage

from agent.nodes import AgentNodes
from schemas.chat import ChatRequest, ChatResponse
from services.chat_service import (
    MAX_REPLY_CHARACTERS,
    filter_tools_for_user,
    validate_assistant_reply,
)


def make_tool(name):
    return SimpleNamespace(name=name)


def test_chat_request_rejects_blank_input_and_trims_valid_input():
    with pytest.raises(ValidationError):
        ChatRequest(message="   ")

    request = ChatRequest(message="  Show my profile  ")
    assert request.message == "Show my profile"


def test_only_role_allowed_tools_are_given_to_the_agent():
    discovered_tools = [
        make_tool("get_my_profile"),
        make_tool("get_my_leave_balance"),
        make_tool("approve_leave"),
        make_tool("deactivate_employee"),
        make_tool("unknown_new_tool"),
    ]

    allowed_tools = filter_tools_for_user(
        discovered_tools,
        {"EMPLOYEE"},
    )

    assert [tool.name for tool in allowed_tools] == [
        "get_my_profile",
        "get_my_leave_balance",
    ]


def test_output_validation_rejects_blank_and_oversized_replies():
    with pytest.raises(ValueError, match="empty"):
        validate_assistant_reply("  ")

    with pytest.raises(ValueError, match="too long"):
        validate_assistant_reply("x" * (MAX_REPLY_CHARACTERS + 1))

    with pytest.raises(ValidationError):
        ChatResponse(session_id=1, reply="")


@pytest.mark.asyncio
async def test_agent_blocks_tool_calls_outside_allow_list():
    class MCPClient:
        async def call_tool(self, *_args, **_kwargs):
            raise AssertionError("The disallowed tool must not be called")

    nodes = AgentNodes(mcp_session=MCPClient(), mcp_tools=[])
    result = await nodes.tool_node(
        {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "deactivate_employee",
                            "args": {"employee_id": 8},
                            "id": "call-blocked",
                            "type": "tool_call",
                        }
                    ],
                )
            ]
        }
    )

    tool_result = result["messages"][0]
    assert tool_result.status == "error"
    assert "not available" in tool_result.content
