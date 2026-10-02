from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.user import User
from models.user_role import UserRole


class UserRepository:

    def __init__(self, db):
        self.db = db


    async def get_by_email(self, email):

        query = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.employee),

                selectinload(User.user_roles)
                .selectinload(UserRole.role)
            )
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()


    async def get_by_id(self, user_id):

        query = (
            select(User)
            .where(User.id == user_id)
            .options(
                # Load employee information
                selectinload(User.employee),

                # Load User -> UserRole -> Role
                selectinload(User.user_roles)
                .selectinload(UserRole.role)
            )
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()