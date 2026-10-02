from models.employee import Employee

from repositories.employee_repository import (
    EmployeeRepository
)

from core.exceptions import (
    EmployeeNotFoundError
)


class HRService:

    def __init__(self, db):

        self.db = db

        self.employee_repository = EmployeeRepository(
            db
        )


    async def get_all_employees(self):

        return await self.employee_repository.get_all()


    async def search_employees(
        self,
        name
    ):

        return await self.employee_repository.search_by_name(
            name
        )


    async def create_employee(
        self,
        request
    ):

        employee = Employee(
            employee_code=request.employee_code,
            firstname=request.firstname,
            lastname=request.lastname,
            email=request.email,
            department_id=request.department_id,
            designation=request.designation,
            manager_id=request.manager_id,
            status="ACTIVE"
        )


        await self.employee_repository.create(
            employee
        )


        await self.employee_repository.commit()


        return employee


    async def deactivate_employee(
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


        # Soft delete
        employee.status = "INACTIVE"


        await self.db.commit()


        return employee