
from sqlalchemy import String

from db.base import Base
from sqlalchemy.orm import Mapped, mapped_column

class Department(Base):

    # Postgres SQL table name
    __tablename__ = 'department'

    id: Mapped[int]= mapped_column(primary_key= True)

    name:Mapped[str] = mapped_column(String(100), unique=True, nullable=False)