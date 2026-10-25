import asyncio
from getpass import getpass

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent


# MCP server address
MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"

# Maximum time to wait
TIMEOUT = 20


# -----------------------------------
# 1. Connect and list MCP tools
# -----------------------------------

async def list_tools(token):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    async with streamablehttp_client(
        MCP_SERVER_URL,
        headers=headers,
        timeout=TIMEOUT
    ) as (read, write, _):

        async with ClientSession(read, write) as session:

            await session.initialize()

            response = await session.list_tools()

            return response.tools


# -----------------------------------
# 2. Call an MCP tool
# -----------------------------------

async def call_tool(token, tool_name, arguments=None):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    if arguments is None:
        arguments = {}

    async with streamablehttp_client(
        MCP_SERVER_URL,
        headers=headers,
        timeout=TIMEOUT
    ) as (read, write, _):

        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )

            if result.isError:
                raise Exception(
                    f"MCP tool failed: {tool_name}"
                )

            return result


# -----------------------------------
# 3. Display tool result
# -----------------------------------

def display_result(result):

    if result.structuredContent is not None:
        print(result.structuredContent)
        return

    for item in result.content:

        if isinstance(item, TextContent):
            print(item.text)


# -----------------------------------
# 4. Main function
# -----------------------------------

async def main():

    token = getpass("Enter JWT token: ").strip()

    if not token:
        print("JWT token is required")
        return

    try:

        print("\nConnecting to MCP server...")

        tools = await asyncio.wait_for(
            list_tools(token),
            timeout=TIMEOUT
        )

        print("\nAvailable MCP tools:")

        for tool in tools:
            print("-", tool.name)

        print("\nCalling get_my_leave_balance...")

        result = await asyncio.wait_for(
            call_tool(
                token=token,
                tool_name="get_my_leave_balance"
            ),
            timeout=TIMEOUT
        )

        print("\nLeave balance:")
        display_result(result)

    except TimeoutError:
        print("MCP server took too long to respond")

    except Exception as error:
        print(f"MCP error: {error}")


if __name__ == "__main__":
    asyncio.run(main())