import asyncio
from getpass import getpass

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent


MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"


async def main():

    # Ask for JWT token
    token = getpass("Enter JWT token: ").strip()

    # Send token to MCP server
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        # Connect to MCP server
        async with asyncio.timeout(20):

            async with streamablehttp_client(
                MCP_SERVER_URL,
                headers=headers,
                timeout=20,
                sse_read_timeout=20
            ) as (read, write, _):

                # Create MCP session
                async with ClientSession(read, write) as session:

                    # Initialize connection
                    await session.initialize()

                    print("MCP connected successfully!")

                    # Discover available tools
                    response = await session.list_tools()

                    print("\nAvailable MCP tools:")

                    for tool in response.tools:
                        print("-", tool.name)

                    # Find the tool we want to test
                    tool_name = "get_my_leave_balance"

                    tool_exists = any(
                        tool.name == tool_name
                        for tool in response.tools
                    )

                    if not tool_exists:
                        print(f"\nTool '{tool_name}' not found")
                        return

                    # Call the tool
                    result = await session.call_tool(
                        tool_name,
                        arguments={}
                    )

                    print("\nTool result:")

                    if result.isError:
                        print("MCP tool returned an error")
                        for item in result.content:
                            if isinstance(item, TextContent):
                                print(item.text)

                    elif result.structuredContent is not None:
                        print(result.structuredContent)

                    else:
                        for item in result.content:
                            if isinstance(item, TextContent):
                                print(item.text)

    except TimeoutError:
        print("MCP connection or tool call timed out")

    except Exception as error:
        print(f"MCP client error: {error}")


if __name__ == "__main__":
    asyncio.run(main())