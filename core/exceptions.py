class AppError(Exception):
    pass


class EmployeeNotFoundError(AppError):
    pass


class UserNotFoundError(AppError):
    pass


class InvalidCredentialsError(AppError):
    pass


class InactiveUserError(AppError):
    pass


class LeaveTypeNotFoundError(AppError):
    pass


class LeaveBalanceNotFoundError(AppError):
    pass


class InsufficientLeaveBalanceError(AppError):
    pass


class InvalidLeaveDateError(AppError):
    pass

class LeaveRequestNotFoundError(AppError):
    pass


class LeaveAlreadyProcessedError(AppError):
    pass


class UnauthorizedLeaveActionError(AppError):
    pass