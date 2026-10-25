from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from agent.state import AgentState
from agent.nodes import AgentNodes


def create_agent(mcp_session, mcp_tools):

    nodes = AgentNodes(
        mcp_session=mcp_session,
        mcp_tools=mcp_tools,
    )

    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("agent", nodes.agent_node)
    graph.add_node("tools", nodes.tool_node)

    # Start with agent
    graph.add_edge(START, "agent")

    # Decide whether tools are required
    def next_step(state):

        last_message = state["messages"][-1]

        if last_message.tool_calls:
            return "tools"

        return END

    graph.add_conditional_edges(
        "agent",
        next_step,
        {
            "tools": "tools",
            END: END,
        },
    )

    # Return tool results to agent
    graph.add_edge("tools", "agent")

    return graph.compile()