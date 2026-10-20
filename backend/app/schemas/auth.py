"""
Authentication Pydantic Schemas.

Module: Core
See: api_contract.md → Authentication
"""


from pydantic import BaseModel, Field

from app.core.enums import UserRole
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """User credentials for login."""

    username: str = Field(min_length=1, description="Username")
    password: str = Field(min_length=1, description="Plain text password")


class LoginResponse(BaseModel):
    """Authentication token response."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration duration in seconds")
    user: UserResponse = Field(description="Authenticated user details")


class TokenPayload(BaseModel):
    """Claims contained within a decoded JWT."""

    sub: str = Field(description="User UUID as subject")
    username: str = Field(description="Username")
    role: UserRole = Field(description="User role")
    exp: int = Field(description="Expiration timestamp")


class ChangePasswordRequest(BaseModel):
    """Payload to update password."""

    current_password: str = Field(min_length=1, description="Current password")
    new_password: str = Field(min_length=8, description="New password")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
