import jwt
from mcp.server.fastmcp import Context

from core.security import decode_access_token
from repositories.user_repository import UserRepository


async def get_authenticated_user(
    ctx: Context,
    db,
    required_role: str | None = "EMPLOYEE",
    require_employee: bool = True,
):
    """Check the request's token and return the matching active user."""

    # MCP gives each tool call a context containing its HTTP request.
    request = ctx.request_context.request
    if request is None:
        raise ValueError("HTTP request is required")

    # The request must include: Authorization: Bearer <token>
    authorization_header = request.headers.get("authorization", "")
    scheme, separator, token = authorization_header.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not token.strip()
    ):
        raise ValueError("Authentication required")

    # Decode the token and read the user's ID from its "sub" field.
    try:
        payload = decode_access_token(token.strip())
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise ValueError("Invalid authentication token")

    # Load the user from the database; never trust a user ID from tool arguments.
    user = await UserRepository(db).get_by_id(user_id)
    if user is None or user.status != "ACTIVE":
        raise ValueError("User is not active")

    # Some tools need a particular role; None means any authenticated role.
    user_roles = [user_role.role.name for user_role in user.user_roles]
    if required_role is not None and required_role not in user_roles:
        role_label = "HR" if required_role == "HR" else required_role.title()
        raise ValueError(f"{role_label} permission required")

    # Most employee tools require the signed-in user to have an employee record.
    if require_employee and user.employee is None:
        raise ValueError("Employee profile not found")

    return user
