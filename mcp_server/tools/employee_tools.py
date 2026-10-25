from mcp.server.fastmcp import Context

from db.session import AsyncSessionLocal
from services.employee_service import EmployeeService
from mcp_server.security import get_authenticated_user


async def get_my_profile(ctx: Context) -> dict:
    """
    Get the authenticated employee's profile.

    Use this tool when an employee asks:
    - Show my profile
    - What is my designation?
    - What is my employee code?
    """

    # Create one database session for this tool call.
    async with AsyncSessionLocal() as db:

        # Identify the authenticated employee.
        user = await get_authenticated_user(
            ctx,
            db,
            required_role=None,
        )

        # Reuse our existing service.
        service = EmployeeService(db)

        employee = await service.get_employee(
            user.employee.id
        )

        # Return only approved profile fields.
        return {
            "employee_id": employee.id,
            "employee_code": employee.employee_code,
            "first_name": employee.firstname,
            "last_name": employee.lastname,
            "email": employee.email,
            "designation": employee.designation,
            "department_id": employee.department_id,
            "status": employee.status
        }