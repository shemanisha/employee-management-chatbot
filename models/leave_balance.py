
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    leave_id : Mapped[int] = mapped_column(ForeignKey("leave.id"), nullable=False)
    allocated: Mapped[int] = mapped_column(nullable=False)
    used: Mapped[int] = mapped_column(nullable=False)