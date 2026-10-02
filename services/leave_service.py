from models.leave_request import LeaveRequest

from repositories.leave_repository import (
    LeaveRepository
)

from repositories.employee_repository import (
    EmployeeRepository
)

from core.exceptions import (
    LeaveTypeNotFoundError,
    LeaveBalanceNotFoundError,
    InsufficientLeaveBalanceError,
    InvalidLeaveDateError,
    LeaveRequestNotFoundError,
    LeaveAlreadyProcessedError,
    UnauthorizedLeaveActionError
)


class LeaveService:

    def __init__(self, db):

        self.db = db

        self.leave_repository = LeaveRepository(db)

        self.employee_repository = EmployeeRepository(db)


    async def get_leave_balance(
        self,
        employee_id
    ):
        """
        Get employee leave balances.
        """

        balances = await self.leave_repository.get_all_balances(
            employee_id
        )

        return balances


    async def get_my_requests(
        self,
        employee_id
    ):
        """
        Get employee's own leave requests.
        """

        requests = await self.leave_repository.get_employee_requests(
            employee_id
        )

        return requests


    async def apply_leave(
        self,
        employee_id,
        leave_type_code,
        start_date,
        end_date,
        reason
    ):

        # End date cannot be before start date
        if end_date < start_date:

            raise InvalidLeaveDateError(
                "End date cannot be before start date"
            )


        # Find leave type
        leave_type = await self.leave_repository.get_leave_type(
            leave_type_code.upper()
        )

        if leave_type is None:

            raise LeaveTypeNotFoundError(
                "Leave type not found"
            )


        # Calculate requested days
        requested_days = (
            end_date - start_date
        ).days + 1


        # Get leave balance
        balance = await self.leave_repository.get_balance(
            employee_id,
            leave_type.id,
            start_date.year
        )


        if balance is None:

            raise LeaveBalanceNotFoundError(
                "Leave balance not found"
            )


        remaining = (
            balance.total - balance.used
        )


        if requested_days > remaining:

            raise InsufficientLeaveBalanceError(
                "Insufficient leave balance"
            )


        # Create leave request
        leave_request = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=leave_type.id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="PENDING"
        )


        await self.leave_repository.create_leave_request(
            leave_request
        )


        await self.leave_repository.commit()


        return leave_request


    async def approve_leave(
        self,
        request_id,
        manager_id
    ):
        """
        Manager approves leave.

        Important:
        Manager can only approve leave belonging
        to their own team.
        """

        # Find leave request
        leave_request = await self.leave_repository.get_request_by_id(
            request_id
        )


        if leave_request is None:

            raise LeaveRequestNotFoundError(
                "Leave request not found"
            )


        # Find employee who requested leave
        employee = await self.employee_repository.get_by_id(
            leave_request.employee_id
        )


        # SECURITY CHECK
        #
        # Is this employee actually managed by
        # the current manager?
        if employee.manager_id != manager_id:

            raise UnauthorizedLeaveActionError(
                "You cannot approve this employee's leave"
            )


        # Only PENDING requests can be approved
        if leave_request.status != "PENDING":

            raise LeaveAlreadyProcessedError(
                "Leave request has already been processed"
            )


        leave_request.status = "APPROVED"

        leave_request.approved_by = manager_id


        await self.db.commit()


        return leave_request


    async def reject_leave(
        self,
        request_id,
        manager_id
    ):
        """
        Manager rejects leave.
        """

        leave_request = await self.leave_repository.get_request_by_id(
            request_id
        )


        if leave_request is None:

            raise LeaveRequestNotFoundError(
                "Leave request not found"
            )


        employee = await self.employee_repository.get_by_id(
            leave_request.employee_id
        )


        # Manager can only reject their team's leave
        if employee.manager_id != manager_id:

            raise UnauthorizedLeaveActionError(
                "You cannot reject this employee's leave"
            )


        if leave_request.status != "PENDING":

            raise LeaveAlreadyProcessedError(
                "Leave request has already been processed"
            )


        leave_request.status = "REJECTED"

        leave_request.approved_by = manager_id


        await self.db.commit()


        return leave_request