from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from models.user import User


router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    employee = current_user.employee

    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "first_name": employee.firstname,
        "last_name": employee.lastname,
        "email": employee.email,
        "designation": employee.designation,
        "department_id": employee.department_id,
    }