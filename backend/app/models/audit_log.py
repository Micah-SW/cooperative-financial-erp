"""
AuditLog ORM Model.

Entity: AuditLog
Schema: coop.audit_log
Module: Core

See: database_schema.md → coop.audit_log
See: domain_model.md → AuditLog

Business Rules:
    - Audit logs are NEVER deleted or modified
    - All financial mutations and sensitive administrative events MUST produce an audit log entry
    - old_values and new_values stored as JSON/JSONB
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CoopBase

if TYPE_CHECKING:
    from app.models.user import User

JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


class AuditLog(CoopBase):
    """Append-only audit trail record."""

    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'VERIFY', 'REVERSE', 'APPROVE', "
            "'REJECT', 'EXIT', 'DEACTIVATE', 'LOGIN', 'CONFIG_CHANGE')",
            name="ck_audit_log_action",
        ),
        Index("ix_audit_log_user_id", "user_id"),
        Index("ix_audit_log_entity", "entity_type", "entity_id"),
        Index("ix_audit_log_created_at", text("created_at DESC")),
        {"schema": "coop"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("coop.users.id"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    old_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON_TYPE,
        nullable=True,
    )
    new_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON_TYPE,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
