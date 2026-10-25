from sqlalchemy import select

from models.employee import Employee


class EmployeeRepository:
    """Run database queries for employee records."""

    def __init__(self, db):
        # Keep the database session so each method can use it for a query.
        self.db = db

    async def get_by_id(self, employee_id):
        """Find one employee by their database ID."""
        query = select(Employee).where(Employee.id == employee_id)
        result = await self.db.execute(query)

        # Return an Employee, or None if no matching row exists.
        return result.scalar_one_or_none()

    async def get_manager(self, manager_id):
        """Find a manager by the manager's employee ID."""
        query = select(Employee).where(Employee.id == manager_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_team(self, manager_id):
        """Find all employees whose manager_id matches this manager."""
        query = select(Employee).where(Employee.manager_id == manager_id)
        result = await self.db.execute(query)

        # A manager can have multiple employees, so return all matching rows.
        return result.scalars().all()

    async def get_all(self):
        """Return every employee record."""
        query = select(Employee)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_by_name(self, name):
        """Find employees whose first name contains the search text."""
        query = select(Employee).where(Employee.firstname.ilike(f"%{name}%"))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, employee):
        """Add an employee to the current database session."""
        self.db.add(employee)

        # Flush sends the insert to the database so generated values are set.
        # The caller decides when to commit the transaction.
        await self.db.flush()
        return employee

    async def commit(self):
        """Save the current database transaction."""
        await self.db.commit()
