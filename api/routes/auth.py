from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token
from db.session import get_db
from repositories.user_repository import UserRepository
from schemas.auth import LoginRequest, TokenResponse
from services.user_service import UserService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    repository = UserRepository(db)

    service = UserService(repository)

    user = await service.authenticate(
        email=request.email,
        password=request.password,
    )

    token = create_access_token(
        user_id=user.id
    )

    return TokenResponse(
        access_token=token
    )