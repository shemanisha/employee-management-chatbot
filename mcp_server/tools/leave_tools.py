from datetime import date

from mcp.server.fastmcp import Context

from db.session import AsyncSessionLocal
from mcp_server.security import get_authenticated_user
from schemas.leave import LeaveRequestCreate
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


async def get_my_leave_balance(ctx: Context) -> list[dict]:
    """Get the authenticated employee's leave balances."""
    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="EMPLOYEE",
        )
        balances = await LeaveService(db).get_leave_balance(user.employee.id)
        return [
            {
                "leave_type_id": balance.leave_type_id,
                "total": balance.total,
                "used": balance.used,
                "remaining": balance.total - balance.used,
            }
            for balance in balances
        ]


async def get_my_leave_requests(ctx: Context) -> list[dict]:
    """List leave requests submitted by the authenticated employee."""
    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="EMPLOYEE",
        )
        requests = await LeaveService(db).get_my_requests(user.employee.id)
        return [_leave_request_data(request) for request in requests]


async def apply_leave(
    ctx: Context,
    leave_type: str,
    start_date: date,
    end_date: date,
    reason: str | None = None,
) -> dict:
    """Submit a leave request for the authenticated employee."""
    leave_data = LeaveRequestCreate(
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )

    async with AsyncSessionLocal() as db:
        user = await get_authenticated_user(
            ctx,
            db,
            required_role="EMPLOYEE",
        )
        request = await LeaveService(db).apply_leave(
            employee_id=user.employee.id,
            leave_type_code=leave_data.leave_type,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            reason=leave_data.reason,
        )
        return {
            "message": "Leave request submitted",
            "leave_request_id": request.id,
            "status": request.status,
        }
