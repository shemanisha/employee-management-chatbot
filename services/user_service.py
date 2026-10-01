from core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)
from core.security import verify_password
from repositories.user_repository import UserRepository


class UserService:

    def __init__(
        self,
        repository: UserRepository,
    ):
        self.repository = repository

    async def authenticate(
        self,
        email: str,
        password: str,
    ):
        user = await self.repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise InvalidCredentialsError()

        if user.status != "ACTIVE":
            raise InactiveUserError(
                "User account is inactive"
            )

        return user