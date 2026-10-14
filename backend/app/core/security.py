"""
Authentication and Security Utilities.

Responsibility:
    - Password hashing and verification (bcrypt)
    - JWT token creation and decoding
    - Token payload structure

Dependencies:
    - passlib[bcrypt]
    - python-jose[cryptography]
    - app.config.settings (SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES)

Must NOT:
    - Access the database directly
    - Contain user lookup logic (that belongs in AuthService)
    - Store tokens or sessions

TODO (Gemini):
    - Implement hash_password(plain: str) -> str
    - Implement verify_password(plain: str, hashed: str) -> bool
    - Implement create_access_token(data: dict) -> str
        - Payload: {"sub": user_id, "username": ..., "role": ..., "exp": ...}
    - Implement decode_access_token(token: str) -> TokenPayload
        - Raises: AuthorizationError on invalid/expired token
    - Use passlib CryptContext with bcrypt scheme
    - Use python-jose for JWT encode/decode
"""


class PasswordHasher:
    """
    Handles bcrypt password hashing and verification.

    TODO (Gemini): Implement using passlib.context.CryptContext
    """
    pass


class TokenManager:
    """
    Handles JWT creation and validation.

    TODO (Gemini): Implement using python-jose
    """
    pass
