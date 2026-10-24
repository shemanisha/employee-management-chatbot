import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.tools.employee_tools import get_my_profile
from mcp_server.tools.hr_tools import (
    create_employee,
    deactivate_employee,
    get_all_employees,
    search_employees,
)
from mcp_server.tools.leave_tools import (
    apply_leave,
    get_my_leave_balance,
    get_my_leave_requests,
)
from mcp_server.tools.manager_tools import (
    approve_leave,
    get_my_manager,
    get_my_team,
    get_pending_leaves,
    reject_leave,
)


mcp = FastMCP(
    name="employee-management-mcp",
    host="127.0.0.1",
    port=8001
)


@mcp.tool()
async def health_check() -> str:
    """Check whether the MCP server is running."""

    return "MCP server is running"


for tool in (
    get_my_profile,
    get_my_manager,
    get_my_leave_balance,
    get_my_leave_requests,
    apply_leave,
    get_my_team,
    get_pending_leaves,
    approve_leave,
    reject_leave,
    get_all_employees,
    search_employees,
    create_employee,
    deactivate_employee,
):
    mcp.tool()(tool)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http"
    )