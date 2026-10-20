"""
User Administration API Router.

Endpoints:
    GET   /               — List users (ADMIN only)
    POST  /               — Create user (ADMIN only)
    GET   /{id}           — User details (ADMIN only)
    PATCH /{id}           — Update user (ADMIN only)
    POST  /{id}/deactivate — Deactivate user (ADMIN only)

See: MODULE_MAP.md → Admin Module
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.core.enums import UserRole
from app.core.pagination import PaginatedResult
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import auth_service

router = APIRouter()


@router.get("", response_model=PaginatedResult[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResult[UserResponse]:
    """List system users with pagination (ADMIN only)."""
    paged = await auth_service.list_users(db, page=page, per_page=per_page)
    return PaginatedResult[UserResponse](
        items=[UserResponse.model_validate(u) for u in paged.items],
        total=paged.total,
        page=paged.page,
        per_page=paged.per_page,
        pages=paged.pages,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    request: Request,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new system user (ADMIN only)."""
    client_ip = request.client.host if request.client else None
    user = await auth_service.create_user(
        db,
        data=payload,
        creator_id=admin_user.id,
        ip_address=client_ip,
    )
    await db.commit()
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieve user details by UUID (ADMIN only)."""
    user = await auth_service.get_user_by_id(db, user_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    request: Request,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update user information (ADMIN only)."""
    client_ip = request.client.host if request.client else None
    user = await auth_service.update_user(
        db,
        user_id=user_id,
        data=payload,
        actor_id=admin_user.id,
        ip_address=client_ip,
    )
    await db.commit()
    return UserResponse.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Deactivate a user account (ADMIN only)."""
    client_ip = request.client.host if request.client else None
    user = await auth_service.deactivate_user(
        db,
        user_id=user_id,
        actor_id=admin_user.id,
        ip_address=client_ip,
    )
    await db.commit()
    return UserResponse.model_validate(user)
