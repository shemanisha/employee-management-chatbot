from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import employee_only

from db.session import get_db

from services.employee_service import EmployeeService


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


@router.get("/me")
async def get_my_profile(
    current_user=Depends(employee_only)
):

    # Employee comes from authenticated user
    employee = current_user.employee

    if employee is None:
        return {
            "message": "Employee profile not found"
        }


    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "first_name": employee.firstname,
        "last_name": employee.lastname,
        "email": employee.email,
        "designation": employee.designation,
        "department_id": employee.department_id
    }


@router.get("/me/manager")
async def get_my_manager(
    current_user=Depends(employee_only),
    db: AsyncSession=Depends(get_db)
):

    employee = current_user.employee

    service = EmployeeService(db)


    manager = await service.get_manager(
        employee
    )


    if manager is None:

        return {
            "message": "No manager assigned"
        }


    return {
        "id": manager.id,
        "employee_code": manager.employee_code,
        "name": manager.firstname + " " + manager.lastname,
        "email": manager.email,
        "designation": manager.designation
    }