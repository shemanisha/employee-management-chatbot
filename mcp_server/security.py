import jwt
from mcp.server.fastmcp import Context

from core.security import decode_access_token
from repositories.user_repository import UserRepository


async def get_authenticated_user(
    ctx: Context,
    db,
    required_role: str = "EMPLOYEE",
    require_employee: bool = True,
):
    request = ctx.request_context.request
    if request is None:
        raise ValueError("HTTP request is required")

    authorization = request.headers.get("authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise ValueError("Authentication required")

    try:
        payload = decode_access_token(token.strip())
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise ValueError("Invalid authentication token")

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or user.status != "ACTIVE":
        raise ValueError("User is not active")

    roles = [item.role.name for item in user.user_roles]
    if required_role not in roles:
        role_label = "HR" if required_role == "HR" else required_role.title()
        raise ValueError(f"{role_label} permission required")

    if require_employee and user.employee is None:
        raise ValueError("Employee profile not found")

    return user
