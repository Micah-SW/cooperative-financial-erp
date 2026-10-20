"""
Audit Logs API Router.

Endpoints:
    GET / — Query audit logs with pagination and filters (ADMIN only)

See: api_contract.md & MODULE_MAP.md
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_service
from app.core.dependencies import get_db, require_role
from app.core.enums import AuditAction, UserRole
from app.core.pagination import PaginatedResult
from app.models.user import User
from app.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("", response_model=PaginatedResult[AuditLogResponse])
async def list_audit_logs(
    user_id: uuid.UUID | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResult[AuditLogResponse]:
    """Query system audit trail entries (ADMIN only)."""
    filters = {
        "user_id": user_id,
        "entity_type": entity_type,
        "action": action,
        "entity_id": entity_id,
        "from_date": from_date,
        "to_date": to_date,
    }
    paged = await audit_service.list_logs(db, filters=filters, page=page, per_page=per_page)
    return PaginatedResult[AuditLogResponse](
        items=[AuditLogResponse.model_validate(entry) for entry in paged.items],
        total=paged.total,
        page=paged.page,
        per_page=paged.per_page,
        pages=paged.pages,
    )
