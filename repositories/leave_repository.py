from sqlalchemy import select

from models.employee import Employee
from models.leave_type import LeaveType
from models.leave_balance import LeaveBalance
from models.leave_request import LeaveRequest


class LeaveRepository:

    def __init__(self, db):
        self.db = db


    async def get_leave_type(self, code):

        query = select(LeaveType).where(
            LeaveType.code == code
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()


    async def get_balance(
        self,
        employee_id,
        leave_type_id,
        year
    ):

        query = select(LeaveBalance).where(

            LeaveBalance.employee_id == employee_id,

            LeaveBalance.leave_type_id == leave_type_id,

            LeaveBalance.year == year
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()


    async def get_all_balances(
        self,
        employee_id
    ):
        """
        Get all leave balances belonging to an employee.
        """

        query = select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id
        )

        result = await self.db.execute(query)

        return result.scalars().all()


    async def get_employee_requests(
        self,
        employee_id
    ):
        """
        Get leave requests belonging to an employee.
        """

        query = select(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id
        )

        result = await self.db.execute(query)

        return result.scalars().all()


    async def get_request_by_id(
        self,
        request_id
    ):
        """
        Find one leave request.
        """

        query = select(LeaveRequest).where(
            LeaveRequest.id == request_id
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()


    async def get_pending_team_requests(
        self,
        manager_id
    ):
        """
        Get pending leave requests ONLY for
        employees reporting to this manager.
        """

        query = (
            select(LeaveRequest)

            .join(
                Employee,
                LeaveRequest.employee_id == Employee.id
            )

            .where(
                Employee.manager_id == manager_id,
                LeaveRequest.status == "PENDING"
            )
        )

        result = await self.db.execute(query)

        return result.scalars().all()


    async def create_leave_request(
        self,
        leave_request
    ):

        self.db.add(leave_request)

        await self.db.flush()

        return leave_request


    async def commit(self):

        await self.db.commit()