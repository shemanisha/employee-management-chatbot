from sqlalchemy import select

from models.employee import Employee


class EmployeeRepository:

    def __init__(self, db):
        self.db = db


    async def get_by_id(self, employee_id):
        """
        Find one employee.
        """

        query = select(Employee).where(
            Employee.id == employee_id
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()


    async def get_manager(self, manager_id):
        """
        Find employee's manager.
        """

        query = select(Employee).where(
            Employee.id == manager_id
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()


    async def get_team(self, manager_id):
        """
        Find employees reporting to this manager.
        """

        query = select(Employee).where(
            Employee.manager_id == manager_id
        )

        result = await self.db.execute(query)

        return result.scalars().all()


    async def get_all(self):
        """
        HR can view all employees.
        """

        query = select(Employee)

        result = await self.db.execute(query)

        return result.scalars().all()


    async def search_by_name(self, name):
        """
        Search employee by first name.
        """

        query = select(Employee).where(
            Employee.firstname.ilike(
                f"%{name}%"
            )
        )

        result = await self.db.execute(query)

        return result.scalars().all()


    async def create(self, employee):
        """
        Add new employee.
        """

        self.db.add(employee)

        await self.db.flush()

        return employee


    async def commit(self):
        """
        Save database changes.
        """

        await self.db.commit()