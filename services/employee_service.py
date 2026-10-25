from core.exceptions import EmployeeNotFoundError
from repositories.employee_repository import EmployeeRepository


class EmployeeService:
    """Apply employee-related business rules."""

    def __init__(self, db):
        # The service uses the repository to read employees from the database.
        self.employee_repository = EmployeeRepository(db)

    async def get_employee(self, employee_id):
        """Return one employee, or raise an error if they do not exist."""
        employee = await self.employee_repository.get_by_id(employee_id)

        if employee is None:
            raise EmployeeNotFoundError("Employee not found")

        return employee

    async def get_manager(self, employee):
        """Return an employee's manager, if one has been assigned."""
        # No database lookup is needed when the employee has no manager.
        if employee.manager_id is None:
            return None

        return await self.employee_repository.get_manager(employee.manager_id)

    async def get_team(self, manager_id):
        """Return all employees who report to the given manager."""
        return await self.employee_repository.get_team(manager_id)
