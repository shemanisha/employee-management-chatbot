from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import employee_only

from db.session import get_db

from schemas.leave import LeaveRequestCreate

from services.leave_service import LeaveService


router = APIRouter(
    prefix="/leaves",
    tags=["Leaves"]
)


@router.get("/balance")
async def get_my_leave_balance(
    current_user=Depends(employee_only),
    db: AsyncSession=Depends(get_db)
):

    # Employee comes from JWT user
    employee = current_user.employee


    service = LeaveService(db)


    balances = await service.get_leave_balance(
        employee.id
    )


    response = []


    for balance in balances:

        remaining = (
            balance.total - balance.used
        )


        response.append({
            "leave_type_id": balance.leave_type_id,
            "total": balance.total,
            "used": balance.used,
            "remaining": remaining
        })


    return response


@router.get("/me")
async def get_my_leave_requests(
    current_user=Depends(employee_only),
    db: AsyncSession=Depends(get_db)
):

    employee = current_user.employee


    service = LeaveService(db)


    requests = await service.get_my_requests(
        employee.id
    )


    return requests


@router.post("")
async def apply_leave(
    request: LeaveRequestCreate,
    current_user=Depends(employee_only),
    db: AsyncSession=Depends(get_db)
):

    employee = current_user.employee


    service = LeaveService(db)


    leave_request = await service.apply_leave(

        # IMPORTANT:
        # Employee ID comes from JWT
        # and NOT request body.
        employee_id=employee.id,

        leave_type_code=request.leave_type,

        start_date=request.start_date,

        end_date=request.end_date,

        reason=request.reason
    )


    return {
        "message": "Leave request submitted",
        "leave_request_id": leave_request.id,
        "status": leave_request.status
    }