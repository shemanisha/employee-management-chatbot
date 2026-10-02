from core.exceptions import EmployeeNotFoundError

from repositories.employee_repository import (
    EmployeeRepository
)


class EmployeeService:

    def __init__(self, db):

        self.employee_repository = EmployeeRepository(
            db
        )


    async def get_employee(
        self,
        employee_id
    ):

        employee = await self.employee_repository.get_by_id(
            employee_id
        )

        if employee is None:
            raise EmployeeNotFoundError(
                "Employee not found"
            )

        return employee


    async def get_manager(
        self,
        employee
    ):
        """
        Get manager belonging to an employee.
        """

        if employee.manager_id is None:
            return None

        manager = await self.employee_repository.get_manager(
            employee.manager_id
        )

        return manager


    async def get_team(
        self,
        manager_id
    ):
        """
        Get employees reporting to manager.
        """

        team = await self.employee_repository.get_team(
            manager_id
        )

        return team