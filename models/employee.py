from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, String, Integer
from db.base import Base



class Employee(Base):

    # Postgres SQL table name
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)

    firstname: Mapped[str] = mapped_column(String(100), nullable=False)

    lastname: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    employee_code:Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    designation:Mapped[str] = mapped_column(String(100),nullable=False)


    department_id: Mapped[int] = mapped_column(ForeignKey('department.id'), nullable=False)

    manager_id: Mapped[int] = mapped_column(ForeignKey('employee.id'), nullable=True)

    status: Mapped[str] = mapped_column(String(10), default='ACTIVE')

    # Gives us:
    # employees.user
    user = relationship(
        "User",
        back_populates="employee",
        uselist=False
    )