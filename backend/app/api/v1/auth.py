"""
Auth API Router.

Endpoints:
    POST /login           — Authenticate user, return JWT
    GET  /me              — Current user profile
    POST /change-password — Change password

See: api_contract.md → Authentication
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate with username and password to receive a JWT access token."""
    client_ip = request.client.host if request.client else None
    token, user = await auth_service.authenticate(
        db,
        username=payload.username,
        password=payload.password,
        ip_address=client_ip,
    )
    await db.commit()

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve profile of currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Update current user's password."""
    client_ip = request.client.host if request.client else None
    await auth_service.change_password(
        db,
        user_id=current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
        ip_address=client_ip,
    )
    await db.commit()
    return MessageResponse(message="Password updated successfully")
