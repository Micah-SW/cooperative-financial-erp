"""
User ORM Model.

Entity: User
Schema: coop.users
Module: Core

See: database_schema.md → coop.users
See: domain_model.md → User
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserRole
from app.models.base import CoopBase

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.system_config import SystemConfig


class User(CoopBase):
    """User account model for system access."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "role IN ('ADMIN', 'TREASURER', 'VIEWER')",
            name="ck_users_role",
        ),
        Index("ix_users_role", "role"),
        {"schema": "coop"},
    )

    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        passive_deletes=True,
    )
    created_configs: Mapped[list["SystemConfig"]] = relationship(
        "SystemConfig",
        back_populates="creator",
    )
