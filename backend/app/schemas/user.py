"""
User Pydantic Schemas.

Module: Core
See: api_contract.md → Users
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import UserRole

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="Unique username")
    email: str = Field(pattern=EMAIL_REGEX, max_length=255, description="Unique email address")
    full_name: str = Field(min_length=1, max_length=100, description="Full display name")
    role: UserRole = Field(description="Role-based permission level")


class UserCreate(UserBase):
    password: str = Field(min_length=8, description="Initial plain text password")


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, pattern=EMAIL_REGEX, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: UserRole | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str
    role: UserRole
    is_active: bool


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    last_login: datetime | None = None
    created_at: datetime
