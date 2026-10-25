import asyncio
import json
import logging

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    SystemMessage,
    ToolMessage,
)

from agent.llm import get_llm
from agent.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentNodes:

    def __init__(self, mcp_session, mcp_tools):

        # Existing authenticated MCP session
        self.mcp_session = mcp_session
        self.allowed_tool_names = {
            tool.name
            for tool in mcp_tools
        }

        # Convert MCP tools into Ollama tool definitions
        tool_definitions = []

        for tool in mcp_tools:

            tool_definitions.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            })

        # Give Ollama the available tool definitions
        self.llm = get_llm().bind_tools(tool_definitions)

    # ----------------------------
    # Agent node
    # ----------------------------

    async def agent_node(self, state):

        messages = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]

        messages.extend(state["messages"])

        try:
            response: AIMessageChunk | None = None

            async with asyncio.timeout(60):
                async for chunk in self.llm.astream(messages):
                    if response is None:
                        response = chunk
                    else:
                        response += chunk

            if response is None:
                raise RuntimeError("The model returned no response")

            completed_message = AIMessage(
                **response.model_dump(
                    exclude={"type", "tool_call_chunks"},
                )
            )
            return {"messages": [completed_message]}

        except TimeoutError:
            logger.warning("Ollama timed out")
            raise RuntimeError("Ollama request timed out")

    # ----------------------------
    # MCP tool node
    # ----------------------------

    async def tool_node(self, state):

        last_message = state["messages"][-1]

        tool_results = []

        for tool_call in last_message.tool_calls:

            tool_name = tool_call["name"]
            arguments = tool_call["args"]
            tool_call_id = tool_call["id"]

            if tool_name not in self.allowed_tool_names:
                logger.warning("Blocked MCP tool not in the allow-list: %s", tool_name)
                tool_results.append(
                    ToolMessage(
                        content='{"error":"This tool is not available."}',
                        tool_call_id=tool_call_id,
                        name=tool_name,
                        status="error",
                    )
                )
                continue

            if not isinstance(arguments, dict):
                logger.warning("Blocked MCP tool call with invalid arguments")
                tool_results.append(
                    ToolMessage(
                        content='{"error":"Tool arguments must be an object."}',
                        tool_call_id=tool_call_id,
                        name=tool_name,
                        status="error",
                    )
                )
                continue

            print(f"\nCalling MCP tool: {tool_name}")
            print("Arguments:", arguments)

            try:
                result = await asyncio.wait_for(
                    self.mcp_session.call_tool(
                        tool_name,
                        arguments=arguments,
                    ),
                    timeout=20,
                )

                if result.isError:
                    error_text = " ".join(
                        getattr(item, "text", "")
                        for item in result.content
                    )

                    content = json.dumps({
                        "error": error_text or "Tool failed"
                    })

                    status = "error"

                elif result.structuredContent is not None:
                    content = json.dumps(
                        result.structuredContent,
                        default=str,
                    )
                    status = "success"

                else:
                    content = json.dumps(
                        [
                            item.model_dump(mode="json")
                            for item in result.content
                        ]
                    )
                    status = "success"

            except TimeoutError:
                content = json.dumps({
                    "error": (
                        "Tool timed out. The result is unknown. "
                        "Do not automatically retry this operation."
                    )
                })
                status = "error"

            except Exception:
                logger.exception("MCP tool execution failed")

                content = json.dumps({
                    "error": "Unable to execute MCP tool"
                })
                status = "error"

            tool_results.append(
                ToolMessage(
                    content=content,
                    tool_call_id=tool_call_id,
                    name=tool_name,
                    status=status,
                )
            )

        return {"messages": tool_results}