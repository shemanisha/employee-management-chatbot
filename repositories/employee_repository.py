from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.employee import Employee


class EmployeeRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        employee_id: int,
    ) -> Employee | None:

        result = await self.db.execute(
            select(Employee).where(
                Employee.id == employee_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        employee_code: str,
    ) -> Employee | None:

        result = await self.db.execute(
            select(Employee).where(
                Employee.employee_code == employee_code
            )
        )

        return result.scalar_one_or_none()

    async def get_manager(
        self,
        employee: Employee,
    ) -> Employee | None:

        if employee.manager_id is None:
            return None

        return await self.get_by_id(employee.manager_id)