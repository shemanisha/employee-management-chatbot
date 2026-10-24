from mcp.server.fastmcp import Context

from db.session import AsyncSessionLocal
from mcp_server.security import get_authenticated_user
from schemas.employee import EmployeeCreateRequest
from services.hr_service import HRService


def _employee_data(employee) -> dict:
    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "first_name": employee.firstname,
        "last_name": employee.lastname,
        "email": employee.email,
        "department_id": employee.department_id,
        "designation": employee.designation,
        "manager_id": employee.manager_id,
        "status": employee.status,
    }


async def get_all_employees(ctx: Context) -> list[dict]:
    """List all employees. HR permission is required."""
    async with AsyncSessionLocal() as db:
        await get_authenticated_user(
            ctx,
            db,
            required_role="HR",
            require_employee=False,
        )
        employees = await HRService(db).get_all_employees()
        return [_employee_data(employee) for employee in employees]


async def search_employees(ctx: Context, name: str) -> list[dict]:
    """Search employees by first name. HR permission is required."""
    async with AsyncSessionLocal() as db:
        await get_authenticated_user(
            ctx,
            db,
            required_role="HR",
            require_employee=False,
        )
        employees = await HRService(db).search_employees(name)
        return [_employee_data(employee) for employee in employees]


async def create_employee(
    ctx: Context,
    employee_code: str,
    firstname: str,
    lastname: str,
    email: str,
    department_id: int,
    designation: str,
    manager_id: int | None = None,
) -> dict:
    """Create an employee record. HR permission is required."""
    request = EmployeeCreateRequest(
        employee_code=employee_code,
        firstname=firstname,
        lastname=lastname,
        email=email,
        department_id=department_id,
        designation=designation,
        manager_id=manager_id,
    )

    async with AsyncSessionLocal() as db:
        await get_authenticated_user(
            ctx,
            db,
            required_role="HR",
            require_employee=False,
        )
        employee = await HRService(db).create_employee(request)
        return {
            "message": "Employee created",
            "employee_id": employee.id,
        }


async def deactivate_employee(ctx: Context, employee_id: int) -> dict:
    """Deactivate an employee account. HR permission is required."""
    async with AsyncSessionLocal() as db:
        await get_authenticated_user(
            ctx,
            db,
            required_role="HR",
            require_employee=False,
        )
        employee = await HRService(db).deactivate_employee(employee_id)
        return {
            "message": "Employee deactivated",
            "employee_id": employee.id,
            "status": employee.status,
        }