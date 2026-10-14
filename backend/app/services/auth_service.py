"""
Authentication Service.

Module: Core
See: service_contracts.md → AuthService (implied)

Responsibility:
    - Authenticate users by username/password
    - Generate JWT tokens
    - Handle password changes

Dependencies:
    - app.core.security (PasswordHasher, TokenManager)
    - app.models.user.User
    - app.core.audit.AuditService

Must NOT:
    - Store sessions or tokens server-side
    - Bypass password hashing
"""


class AuthService:
    """
    Handles user authentication workflows.

    Responsibilities:
        - Validate credentials against stored bcrypt hash
        - Generate JWT token on successful authentication
        - Update last_login timestamp
        - Record LOGIN audit events
        - Handle password change with current password verification

    Must NOT:
        - Access financial data
        - Manage user CRUD (that's admin/user management)
    """

    async def authenticate(self, db, username: str, password: str):
        """
        Validate credentials and return JWT + user info.
        Raises: AuthorizationError on invalid credentials.
        TODO (Gemini): Implement
        """
        pass

    async def change_password(self, db, user_id, current_password: str, new_password: str):
        """
        Change password with current password verification.
        TODO (Gemini): Implement
        """
        pass
