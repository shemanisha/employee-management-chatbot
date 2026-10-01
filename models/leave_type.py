



from db.base import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class LeaveType(Base):
    __tablename__ = "leave_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # CL/SL/EL
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    # Casual Leave/Sick Leave/Earned Leave
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)