from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_access_token
from db.session import get_db
from repositories.user_repository import UserRepository


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id = int(payload["sub"])

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    repository = UserRepository(db)

    user = await repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User does not exist",
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    return user