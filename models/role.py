from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from db.base import Base

class Role(Base):

    __tablename__ = 'roles'

    id :Mapped[int] = mapped_column(primary_key= True)
    name:Mapped[str] = mapped_column(String(20), unique=True, nullable=False)


    # Relationship back to user_roles
    user_roles = relationship(
        "UserRole",
        back_populates="role"
    )
