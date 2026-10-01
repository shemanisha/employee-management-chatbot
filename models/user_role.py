
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey('role.id'), nullable=False)
    