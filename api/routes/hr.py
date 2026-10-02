from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import hr_only

from db.session import get_db

from schemas.employee import EmployeeCreateRequest

from services.hr_service import HRService


router = APIRouter(
    prefix="/hr",
    tags=["HR"]
)


@router.get("/employees")
async def get_all_employees(
    current_user=Depends(hr_only),
    db: AsyncSession=Depends(get_db)
):

    service = HRService(db)

    employees = await service.get_all_employees()

    return employees


@router.get("/employees/search")
async def search_employees(
    name: str,
    current_user=Depends(hr_only),
    db: AsyncSession=Depends(get_db)
):

    service = HRService(db)


    employees = await service.search_employees(
        name
    )


    return employees


@router.post("/employees")
async def create_employee(
    request: EmployeeCreateRequest,
    current_user=Depends(hr_only),
    db: AsyncSession=Depends(get_db)
):

    service = HRService(db)


    employee = await service.create_employee(
        request
    )


    return {
        "message": "Employee created",
        "employee_id": employee.id
    }


@router.patch(
    "/employees/{employee_id}/deactivate"
)
async def deactivate_employee(
    employee_id: int,
    current_user=Depends(hr_only),
    db: AsyncSession=Depends(get_db)
):

    service = HRService(db)


    employee = await service.deactivate_employee(
        employee_id
    )


    return {
        "message": "Employee deactivated",
        "employee_id": employee.id,
        "status": employee.status
    }