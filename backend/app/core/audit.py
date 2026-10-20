"""
Audit Logging Service.

Responsibility:
    - Record all sensitive actions as append-only audit log entries
    - Capture before/after state for mutations
    - Participate in the caller's database transaction (no independent commit)

Audit Contract:
    Every service that mutates persistent data MUST call:
        audit_service.log(db, user_id=..., action=..., entity_type=..., entity_id=..., ...)
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditAction
from app.core.pagination import PaginatedResult, paginate
from app.models.audit_log import AuditLog

# Keys to sanitize to prevent credentials or tokens from being saved in audit logs
SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "password_hash",
    "token",
    "access_token",
    "secret",
    "secret_key",
    "old_password",
    "new_password",
    "current_password",
}


def _sanitize_value(val: Any) -> Any:
    """Sanitize individual values, recursing through nested dicts and lists."""
    if isinstance(val, dict):
        return sanitize_audit_dict(val)
    if isinstance(val, list):
        return [_sanitize_value(item) for item in val]
    if isinstance(val, tuple):
        return tuple(_sanitize_value(item) for item in val)
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, datetime):
        return val.isoformat()
    return val


def sanitize_audit_dict(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Recursively scrub sensitive keys from audit log dictionaries and nested structures."""
    if not data:
        return data

    sanitized: dict[str, Any] = {}
    for k, v in data.items():
        if str(k).lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = _sanitize_value(v)
    return sanitized


class AuditService:
    """
    Append-only audit event recorder.

    Participates in the caller's transaction without committing or rolling back.
    """

    async def log(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        action: AuditAction | str,
        entity_type: str,
        entity_id: uuid.UUID,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """
        Record an immutable audit log entry within the caller's transaction.

        Guarantees sensitive fields are never written to the audit log.
        """
        action_str = action.value if isinstance(action, AuditAction) else str(action)
        clean_old = sanitize_audit_dict(old_values)
        clean_new = sanitize_audit_dict(new_values)

        entry = AuditLog(
            user_id=user_id,
            action=action_str,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=clean_old,
            new_values=clean_new,
            ip_address=ip_address,
        )
        db.add(entry)
        return entry

    async def list_logs(
        self,
        db: AsyncSession,
        *,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> PaginatedResult:
        """Query audit log entries with pagination and optional filters."""
        query = select(AuditLog)
        filters = filters or {}

        if filters.get("user_id"):
            query = query.where(AuditLog.user_id == filters["user_id"])
        if filters.get("entity_type"):
            query = query.where(AuditLog.entity_type == filters["entity_type"])
        if filters.get("action"):
            action_val = (
                filters["action"].value
                if isinstance(filters["action"], AuditAction)
                else str(filters["action"])
            )
            query = query.where(AuditLog.action == action_val)
        if filters.get("entity_id"):
            query = query.where(AuditLog.entity_id == filters["entity_id"])
        if filters.get("from_date"):
            query = query.where(AuditLog.created_at >= filters["from_date"])
        if filters.get("to_date"):
            query = query.where(AuditLog.created_at <= filters["to_date"])

        query = query.order_by(AuditLog.created_at.desc())
        return await paginate(db, query, page=page, per_page=per_page)


audit_service = AuditService()
