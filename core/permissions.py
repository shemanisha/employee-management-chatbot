from fastapi import HTTPException


def get_user_roles(user):
    """
    Return all roles assigned to a user.

    Example:
    Amit -> ["EMPLOYEE", "MANAGER"]
    """

    roles = []

    for user_role in user.user_roles:
        roles.append(user_role.role.name)

    return roles


def require_employee(user):
    """
    Check whether user has employee access.
    """

    roles = get_user_roles(user)

    if "EMPLOYEE" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Employee permission required"
        )

    return user


def require_manager(user):
    """
    Check whether user is a manager.
    """

    roles = get_user_roles(user)

    if "MANAGER" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Manager permission required"
        )

    return user


def require_hr(user):
    """
    Check whether user is HR.
    """

    roles = get_user_roles(user)

    if "HR" not in roles:
        raise HTTPException(
            status_code=403,
            detail="HR permission required"
        )

    return user