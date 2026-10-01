from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.leave_balance import LeaveBalance
from models.leave_request import LeaveRequest
from models.leave_type import LeaveType


class LeaveRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_leave_type_by_code(
        self,
        code: str,
    ) -> LeaveType | None:

        result = await self.db.execute(
            select(LeaveType).where(
                LeaveType.code == code
            )
        )

        return result.scalar_one_or_none()

    async def get_balance(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
    ) -> LeaveBalance | None:

        result = await self.db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year,
            )
        )

        return result.scalar_one_or_none()

    async def create_request(
        self,
        request: LeaveRequest,
    ) -> LeaveRequest:

        self.db.add(request)

        await self.db.flush()
        await self.db.refresh(request)

        return request

    async def commit(self) -> None:
        await self.db.commit()