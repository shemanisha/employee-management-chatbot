from datetime import date

from core.exceptions import (
    InsufficientLeaveBalanceError,
    InvalidLeaveDateError,
    LeaveBalanceNotFoundError,
    LeaveTypeNotFoundError,
)
from models.leave_request import LeaveRequest
from repositories.leave_repository import LeaveRepository


class LeaveService:

    def __init__(
        self,
        repository: LeaveRepository,
    ):
        self.repository = repository

    async def apply_leave(
        self,
        employee_id: int,
        leave_type_code: str,
        start_date: date,
        end_date: date,
        reason: str | None,
    ) -> LeaveRequest:

        if end_date < start_date:
            raise InvalidLeaveDateError(
                "End date cannot be before start date"
            )

        leave_type = (
            await self.repository.get_leave_type_by_code(
                leave_type_code.upper()
            )
        )

        if leave_type is None:
            raise LeaveTypeNotFoundError(
                f"Leave type {leave_type_code} does not exist"
            )

        requested_days = (
            end_date - start_date
        ).days + 1

        balance = await self.repository.get_balance(
            employee_id=employee_id,
            leave_type_id=leave_type.id,
            year=start_date.year,
        )

        if balance is None:
            raise LeaveBalanceNotFoundError(
                "Leave balance not found"
            )

        if requested_days > balance.remaining:
            raise InsufficientLeaveBalanceError(
                f"Only {balance.remaining} leave days are available"
            )

        request = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=leave_type.id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="PENDING",
        )

        request = await self.repository.create_request(request)

        await self.repository.commit()

        return request