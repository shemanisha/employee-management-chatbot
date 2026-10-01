
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), primary_key=True)


    # Relationship back to User
    user = relationship(
        "User",
        back_populates="user_roles"
    )

    # Relationship to Role
    role = relationship(
        "Role",
        back_populates="user_roles"
    )
    