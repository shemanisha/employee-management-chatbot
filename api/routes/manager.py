from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import manager_only

from db.session import get_db

from services.employee_service import EmployeeService
from services.leave_service import LeaveService

from repositories.leave_repository import LeaveRepository


router = APIRouter(
    prefix="/manager",
    tags=["Manager"]
)


@router.get("/team")
async def get_my_team(
    current_user=Depends(manager_only),
    db: AsyncSession=Depends(get_db)
):

    # Logged-in manager's employee record
    manager = current_user.employee


    service = EmployeeService(db)


    team = await service.get_team(
        manager.id
    )


    response = []


    for employee in team:

        response.append({
            "id": employee.id,
            "employee_code": employee.employee_code,
            "name": employee.firstname + " " + employee.lastname,
            "email": employee.email,
            "designation": employee.designation
        })


    return response


@router.get("/leaves/pending")
async def get_pending_leaves(
    current_user=Depends(manager_only),
    db: AsyncSession=Depends(get_db)
):

    manager = current_user.employee


    repository = LeaveRepository(db)


    requests = await repository.get_pending_team_requests(
        manager.id
    )


    return requests


@router.post(
    "/leaves/{request_id}/approve"
)
async def approve_leave(
    request_id: int,
    current_user=Depends(manager_only),
    db: AsyncSession=Depends(get_db)
):

    manager = current_user.employee


    service = LeaveService(db)


    leave_request = await service.approve_leave(
        request_id=request_id,
        manager_id=manager.id
    )


    return {
        "message": "Leave approved",
        "request_id": leave_request.id,
        "status": leave_request.status
    }


@router.post(
    "/leaves/{request_id}/reject"
)
async def reject_leave(
    request_id: int,
    current_user=Depends(manager_only),
    db: AsyncSession=Depends(get_db)
):

    manager = current_user.employee


    service = LeaveService(db)


    leave_request = await service.reject_leave(
        request_id=request_id,
        manager_id=manager.id
    )


    return {
        "message": "Leave rejected",
        "request_id": leave_request.id,
        "status": leave_request.status
    }