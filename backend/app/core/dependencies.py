"""
FastAPI Dependency Injection Functions.

Responsibility:
    - Provide reusable dependencies for FastAPI route handlers
    - Extract and validate the current user from JWT
    - Enforce role-based access control
    - Provide database session dependency

Dependencies:
    - app.database.get_db
    - app.core.security (decode_access_token)
    - app.core.enums.UserRole
    - app.core.exceptions.AuthorizationError

Must NOT:
    - Contain business logic
    - Directly query the database for business data
    - Implement authentication logic (delegate to security module)

TODO (Gemini):
    - Implement get_current_user(token: str = Depends(oauth2_scheme)) -> User
        - Decode JWT
        - Look up user in DB
        - Raise 401 if invalid/expired/user not found/user inactive
    - Implement require_role(*roles: UserRole) -> Callable
        - Returns a dependency that checks current_user.role is in allowed roles
        - Raise 403 if role not authorized
    - Use fastapi.security.OAuth2PasswordBearer for token extraction
    - Pattern: require_role(UserRole.ADMIN, UserRole.TREASURER)
"""

# from fastapi import Depends
# from fastapi.security import OAuth2PasswordBearer

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# async def get_current_user(...) -> User: ...
# def require_role(*roles: UserRole): ...

# TODO: Implement dependencies
