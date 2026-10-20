"""
Authentication and Security Utilities.

Responsibility:
    - Password hashing and verification (bcrypt)
    - JWT token creation and decoding
    - Token payload structure

Dependencies:
    - bcrypt
    - python-jose
    - app.config.settings
    - app.core.exceptions.AuthenticationError
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.core.enums import UserRole
from app.core.exceptions import AuthenticationError
from app.schemas.auth import TokenPayload


class PasswordHasher:
    """Handles bcrypt password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain text password using bcrypt."""
        pwd_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a stored bcrypt hash."""
        if not plain_password or not hashed_password:
            return False
        try:
            pwd_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except (ValueError, TypeError):
            return False


class TokenManager:
    """Handles JWT creation and validation."""

    @staticmethod
    def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed JWT access token."""
        to_encode = data.copy()
        now = datetime.now(UTC)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

        to_encode.update({"exp": int(expire.timestamp())})
        if "sub" in to_encode and not isinstance(to_encode["sub"], str):
            to_encode["sub"] = str(to_encode["sub"])

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> TokenPayload:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            sub = payload.get("sub")
            username = payload.get("username")
            role = payload.get("role")
            exp = payload.get("exp")

            if not sub or not username or not role or not exp:
                raise AuthenticationError("Invalid token payload: missing required claims")

            try:
                user_role = UserRole(role)
            except ValueError:
                raise AuthenticationError(f"Invalid or unsupported role claim in token: '{role}'")

            try:
                exp_int = int(exp)
            except (ValueError, TypeError):
                raise AuthenticationError("Invalid expiration claim in token")

            return TokenPayload(
                sub=str(sub),
                username=str(username),
                role=user_role,
                exp=exp_int,
            )
        except JWTError as e:
            raise AuthenticationError(f"Could not validate token: {e!s}")


def hash_password(password: str) -> str:
    return PasswordHasher.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return PasswordHasher.verify_password(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    return TokenManager.create_access_token(data, expires_delta)


def decode_access_token(token: str) -> TokenPayload:
    return TokenManager.decode_access_token(token)
