"""
Members API Router.

Endpoints:
    GET    /              — List members (ALL roles: ADMIN, TREASURER, VIEWER)
    GET    /{id}          — Member detail (ALL roles: ADMIN, TREASURER, VIEWER)
    POST   /              — Create member (ADMIN only)
    PUT    /{id}          — Update member (ADMIN only)
    PATCH  /{id}          — Update member partial (ADMIN only)
    POST   /{id}/exit     — Process member exit (ADMIN only)

See: api_contract.md → Members
See: service_contracts.md → MemberService
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.core.enums import MemberStatus, UserRole
from app.core.pagination import PaginatedResult
from app.models.user import User
from app.schemas.member import (
    MemberCreate,
    MemberDetail,
    MemberExitRequest,
    MemberSummary,
    MemberUpdate,
)
from app.services.member_service import member_service

router = APIRouter()


@router.get("", response_model=PaginatedResult[MemberSummary])
async def list_members(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(default=25, ge=1, le=100, description="Items per page"),
    status: MemberStatus | None = Query(default=None, description="Filter by member status"),
    search: str | None = Query(default=None, description="Search across member number, name, or phone"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResult[MemberSummary]:
    """Retrieve a paginated directory of cooperative members (ALL authenticated roles)."""
    paged = await member_service.list_members(
        db,
        status=status,
        search=search,
        page=page,
        per_page=per_page,
    )
    return PaginatedResult[MemberSummary](
        items=[MemberSummary.model_validate(m) for m in paged.items],
        total=paged.total,
        page=paged.page,
        per_page=paged.per_page,
        pages=paged.pages,
    )


@router.post("", response_model=MemberDetail, status_code=status.HTTP_201_CREATED)
async def create_member(
    payload: MemberCreate,
    request: Request,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> MemberDetail:
    """Register a new member with initial share allocation (ADMIN only)."""
    client_ip = request.client.host if request.client else None
    member = await member_service.create_member(
        db,
        data=payload,
        user_id=admin_user.id,
        ip_address=client_ip,
    )
    await db.commit()
    return MemberDetail.model_validate(member)


@router.get("/{member_id}", response_model=MemberDetail)
async def get_member_detail(
    member_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberDetail:
    """Retrieve full member profile and share history (ALL authenticated roles)."""
    member = await member_service.get_member(db, member_id)
    return MemberDetail.model_validate(member)


@router.put("/{member_id}", response_model=MemberDetail)
@router.patch("/{member_id}", response_model=MemberDetail)
async def update_member(
    member_id: uuid.UUID,
    payload: MemberUpdate,
    request: Request,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> MemberDetail:
    """Update mutable contact and profile fields for a member (ADMIN only)."""
    client_ip = request.client.host if request.client else None
    member = await member_service.update_member(
        db,
        member_id=member_id,
        data=payload,
        user_id=admin_user.id,
        ip_address=client_ip,
    )
    await db.commit()
    return MemberDetail.model_validate(member)


@router.post("/{member_id}/exit", response_model=MemberDetail)
async def exit_member(
    member_id: uuid.UUID,
    payload: MemberExitRequest,
    request: Request,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> MemberDetail:
    """Process an authorized member exit and extinguish shares (ADMIN only)."""
    client_ip = request.client.host if request.client else None
    member = await member_service.exit_member(
        db,
        member_id=member_id,
        data=payload,
        user_id=admin_user.id,
        ip_address=client_ip,
    )
    await db.commit()
    return MemberDetail.model_validate(member)
