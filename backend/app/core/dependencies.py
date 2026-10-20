"""
FastAPI Dependency Injection Functions.

Responsibility:
    - Provide reusable dependencies for FastAPI route handlers
    - Extract and validate the current user from JWT
    - Enforce role-based access control (RBAC)
    - Provide database session dependency
"""

import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticate the current request via bearer token and load the User.

    Raises:
        AuthenticationError: If token is invalid, expired, user does not exist, or account is disabled.
    """
    payload = decode_access_token(token)
    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError:
        raise AuthenticationError("Invalid subject claim in token")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    return user


def require_role(*roles: UserRole) -> Callable:
    """
    Factory creating a role-enforcement dependency.

    Enforces that the current authenticated user possesses one of the authorized roles.
    Raises:
        AuthorizationError: If the user's role is not in the authorized roles.
    """
    allowed_values = {r.value if hasattr(r, "value") else str(r) for r in roles}

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role_str = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        if user_role_str not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            raise AuthorizationError(
                f"Forbidden: role '{user_role_str}' does not have permission. Required: [{allowed}]"
            )
        return current_user

    return role_checker
