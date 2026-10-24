from mcp.server.fastmcp import Context

from db.session import AsyncSessionLocal
from repositories.leave_repository import LeaveRepository
from mcp_server.security import get_authenticated_user
from services.employee_service import EmployeeService
from services.leave_service import LeaveService


def _leave_request_data(request) -> dict:
    return {
        "id": request.id,
        "employee_id": request.employee_id,
        "leave_type_id": request.leave_type_id,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "reason": request.reason,
        "status": request.status,
        "approved_by": request.approved_by,
    }


async def get_my_manager(ctx: Context) -> dict:
    """Get the authenticated employee's manager."""
    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="EMPLOYEE",
        )
        manager = await EmployeeService(db).get_manager(user.employee)

        if manager is None:
            return {"message": "No manager assigned"}

        return {
            "id": manager.id,
            "name": f"{manager.firstname} {manager.lastname}",
            "email": manager.email,
        }


async def get_my_team(ctx: Context) -> list[dict]:
    """List employees who report to the authenticated manager."""
    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="MANAGER",
        )
        employees = await EmployeeService(db).get_team(user.employee.id)
        return [
            {
                "id": employee.id,
                "employee_code": employee.employee_code,
                "name": f"{employee.firstname} {employee.lastname}",
                "email": employee.email,
                "designation": employee.designation,
            }
            for employee in employees
        ]


async def get_pending_leaves(ctx: Context) -> list[dict]:
    """List pending leave requests from the authenticated manager's team."""
    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="MANAGER",
        )
        requests = await LeaveRepository(db).get_pending_team_requests(
            user.employee.id
        )
        return [_leave_request_data(request) for request in requests]


async def approve_leave(ctx: Context, request_id: int) -> dict:
    """Approve a pending leave request belonging to the manager's team."""
    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="MANAGER",
        )
        request = await LeaveService(db).approve_leave(
            request_id=request_id,
            manager_id=user.employee.id,
        )
        return {
            "message": "Leave approved",
            "request_id": request.id,
            "status": request.status,
        }


async def reject_leave(ctx: Context, request_id: int) -> dict:
    """Reject a pending leave request belonging to the manager's team."""
    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="MANAGER",
        )
        request = await LeaveService(db).reject_leave(
            request_id=request_id,
            manager_id=user.employee.id,
        )
        return {
            "message": "Leave rejected",
            "request_id": request.id,
            "status": request.status,
        }
