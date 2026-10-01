from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey, String, Integer
from db.base import Base



class Employee(Base):

    # Postgres SQL table name
    __tablename__ = 'employee'

    id: Mapped[int] = mapped_column(primary_key=True)

    firstName: Mapped[str] = mapped_column(String(100), nullable=False)

    lastName: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    emp_code:Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    designation:Mapped[str] = mapped_column(String(100),nullable=False)


    department_id: Mapped[int] = mapped_column(ForeignKey('department.id'), nullable=False)

    manager_id: Mapped[int] = mapped_column(ForeignKey('employee.id'), nullable=True)

    active: Mapped[bool] = mapped_column(String(10), default='ACTIVE')