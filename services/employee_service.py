from core.exceptions import EmployeeNotFoundError
from repositories.employee_repository import EmployeeRepository


class EmployeeService:

    def __init__(
        self,
        repository: EmployeeRepository,
    ):
        self.repository = repository

    async def get_employee(
        self,
        employee_id: int,
    ):
        employee = await self.repository.get_by_id(employee_id)

        if employee is None:
            raise EmployeeNotFoundError(
                f"Employee {employee_id} not found"
            )

        return employee

    async def get_manager(
        self,
        employee_id: int,
    ):
        employee = await self.get_employee(employee_id)

        return await self.repository.get_manager(employee)