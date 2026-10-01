from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User
from models.user_role import UserRole


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:

        result = await self.db.execute(
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.user_roles)
                .selectinload(UserRole.role)
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id(
    self,
    user_id: int,
) -> User | None:

        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.employee),
                selectinload(User.user_roles)
                .selectinload(UserRole.role),
            )
        )

        return result.scalar_one_or_none()