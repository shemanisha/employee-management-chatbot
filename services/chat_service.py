import logging
import re

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


MAX_HISTORY_TURNS = 10
MAX_REPLY_CHARACTERS = 8000
SCOPE_FALLBACK_REPLY = (
    "I'm an AI assistant for the Employee Management System. I can help with "
    "leave balances and requests, manager and team information, employee "
    "profiles, and related HR tasks. What would you like help with?"
)
_INTERNAL_TOOL_TEXT = re.compile(
    r"\b(function call|tool call|function to use|tool schema)\b|"
    r'"parameters"\s*:',
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)

# A tool not listed here is never shown to the model.
TOOL_ROLES = {
    "health_check": set(),
    "get_my_profile": set(),
    "get_my_manager": {"EMPLOYEE"},
    "get_my_leave_balance": {"EMPLOYEE"},
    "get_my_leave_requests": {"EMPLOYEE"},
    "apply_leave": {"EMPLOYEE"},
    "get_my_team": {"MANAGER"},
    "get_pending_leaves": {"MANAGER"},
    "approve_leave": {"MANAGER"},
    "reject_leave": {"MANAGER"},
    "get_all_employees": {"HR"},
    "search_employees": {"HR"},
    "create_employee": {"HR"},
    "deactivate_employee": {"HR"},
}


def get_recent_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Keep the latest ten user turns with their full tool-call conversations."""
    user_message_indexes = [
        index
        for index, message in enumerate(messages)
        if isinstance(message, HumanMessage)
    ]

    if len(user_message_indexes) <= MAX_HISTORY_TURNS:
        return messages

    # Keep everything from the oldest of the ten most recent turns onward.
    first_kept_turn = user_message_indexes[-MAX_HISTORY_TURNS]
    return messages[first_kept_turn:]


def filter_tools_for_user(tools, user_roles: set[str]):
    """Only show tools this signed-in user is allowed to use."""
    allowed_tools = []

    for tool in tools:
        required_roles = TOOL_ROLES.get(tool.name)
        if required_roles is None:
            logger.warning("MCP tool is not in the chat allow-list: %s", tool.name)
            continue

        if not required_roles or required_roles.intersection(user_roles):
            allowed_tools.append(tool)

    return allowed_tools


def validate_assistant_reply(reply: str) -> str:
    """Reject empty or unusually large responses before returning them."""
    if not isinstance(reply, str):
        raise ValueError("Assistant response must be text")

    reply = reply.strip()
    if not reply:
        raise ValueError("Assistant returned an empty response")

    if len(reply) > MAX_REPLY_CHARACTERS:
        raise ValueError("Assistant response is too long")

    return reply


def sanitize_assistant_reply(reply: str, tool_names: set[str]) -> str:
    """Replace tool-debugging text with a user-facing product description."""
    reply = validate_assistant_reply(reply)
    normalized_reply = reply.casefold()

    if _INTERNAL_TOOL_TEXT.search(reply) or any(
        tool_name.casefold() in normalized_reply
        for tool_name in tool_names
        if tool_name
    ):
        return SCOPE_FALLBACK_REPLY

    return reply


def message_to_response(message: BaseMessage) -> dict:
    """Convert a LangChain message into a JSON-friendly response."""
    response = {
        "role": message.type,
        "content": message.content,
        "tool_calls": [],
        "tool_call_id": None,
        "tool_name": None,
        "status": None,
    }

    if isinstance(message, AIMessage):
        response["tool_calls"] = message.tool_calls

    if isinstance(message, ToolMessage):
        response["tool_call_id"] = message.tool_call_id
        response["tool_name"] = message.name
        response["status"] = message.status

    return response