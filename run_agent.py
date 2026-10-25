import asyncio
import os
from getpass import getpass

from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from langchain_core.messages import HumanMessage

from agent.graph import create_agent


load_dotenv()


MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")


async def main():

    # Step 1: Get JWT
    token = getpass("Enter JWT token: ").strip()

    if not token:
        print("JWT token is required")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Step 2: Connect to MCP server
    async with streamablehttp_client(
        MCP_SERVER_URL,
        headers=headers,
        timeout=20,
        sse_read_timeout=60,
    ) as (read, write, _):

        async with ClientSession(read, write) as session:

            # Step 3: Initialize MCP
            await session.initialize()

            print("\nMCP connected successfully!")

            # Step 4: Discover MCP tools
            response = await session.list_tools()

            tools = response.tools

            print("\nAvailable MCP tools:")

            for tool in tools:
                print("-", tool.name)

            # Step 5: Create LangGraph agent
            agent = create_agent(
                mcp_session=session,
                mcp_tools=tools,
            )

            print("\nEmployee AI Assistant is ready!")
            print("Type 'exit' to stop.")

            # Step 6: Conversation
            messages = []

            while True:

                question = await asyncio.to_thread(
                    input,
                    "\nYou: "
                )

                if question.lower() == "exit":
                    break

                if not question.strip():
                    continue

                # Add the user question
                messages.append(
                    HumanMessage(content=question)
                )

                try:
                    # Step 7: Run LangGraph
                    result = await agent.ainvoke(
                        {"messages": messages},
                        config={"recursion_limit": 12},
                    )

                    # Update conversation history
                    messages = result["messages"]

                    # Step 8: Show final answer
                    final_message = messages[-1]

                    print("\nAssistant:")
                    print(final_message.content)

                except Exception as error:
                    # Remove the unanswered user question
                    messages.pop()
                    print(f"\nAgent error: {error}")


if __name__ == "__main__":
    asyncio.run(main())