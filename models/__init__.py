# Import every model here so SQLAlchemy knows about them

from models.department import Department
from models.employee import Employee
from models.user import User
from models.role import Role
from models.user_role import UserRole
from models.leave_type import LeaveType
from models.leave_balance import LeaveBalance
from models.leave_request import LeaveRequest