from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


MAX_HISTORY_TURNS = 10


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