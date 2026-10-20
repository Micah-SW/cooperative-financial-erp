"""
SystemConfig ORM Model.

Entity: SystemConfig
Schema: coop.system_config
Module: Core

See: database_schema.md → coop.system_config
See: domain_model.md → SystemConfig

Business Rules:
    - Effective-dated: each record has effective_from and effective_to
    - Only one active record per key (effective_to IS NULL)
    - Changing a value closes the current record and creates a new one
    - Config keys: SHARE_VALUE, SHARES_PER_MEMBER, MEMBER_CONTRIBUTION_AMOUNT,
                   OPERATING_CONTRIBUTION_AMOUNT, COOPERATIVE_NAME, CURRENCY_CODE
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CoopBase

if TYPE_CHECKING:
    from app.models.user import User


class SystemConfig(CoopBase):
    """Effective-dated system configuration entry."""

    __tablename__ = "system_config"
    __table_args__ = (
        UniqueConstraint("config_key", "effective_from", name="uq_system_config_key_effective"),
        CheckConstraint(
            "value_type IN ('DECIMAL', 'INTEGER', 'STRING', 'BOOLEAN')",
            name="ck_system_config_value_type",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_system_config_dates",
        ),
        Index("ix_system_config_lookup", "config_key", "effective_from", "effective_to"),
        {"schema": "coop"},
    )

    config_key: Mapped[str] = mapped_column(String(50), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("coop.users.id"),
        nullable=False,
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_configs")
