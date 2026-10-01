from datetime import date

from sqlalchemy import (
    String,
    Date,
    ForeignKey
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from db.base import Base


class LeaveRequest(Base):

    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False
    )

    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey("leave_types.id"),
        nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # PENDING / APPROVED / REJECTED
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING"
    )

    # Manager who approved/rejected leave
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"),
        nullable=True
    )