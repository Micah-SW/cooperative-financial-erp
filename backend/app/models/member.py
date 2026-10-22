"""
Member ORM Model.

Entity: Member
Schema: coop.members
Module: Member

See: database_schema.md → coop.members
See: domain_model.md → Member
"""

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MemberStatus
from app.models.base import CoopBase

if TYPE_CHECKING:
    from app.models.share import Share
    from app.models.user import User


def _share_sort_key(s: "Share") -> tuple:
    """
    Deterministic sort key for share history snapshots.

    Prioritizes:
      1. effective_date (latest date first)
      2. created_at timestamp (newest first, treating unpersisted as latest)
      3. is_extinguishing flag (share_count == 0 takes precedence on tie)
    """
    created = s.created_at
    if created is None:
        created = datetime.max.replace(tzinfo=UTC)
    elif created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    else:
        created = created.astimezone(UTC)
    is_extinguishing = 1 if s.share_count == 0 else 0
    return (s.effective_date, created, is_extinguishing)


class Member(CoopBase):
    """
    Cooperative member record.

    Invariants:
        - member_number is unique and immutable after creation
        - Lifecycle transition ACTIVE -> EXITED is one-way
        - Historical share allocations are preserved indefinitely
        - Physical deletion is not permitted
    """

    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("member_number", name="uq_members_member_number"),
        CheckConstraint(
            "status IN ('ACTIVE', 'EXITED', 'SUSPENDED')",
            name="ck_members_status",
        ),
        CheckConstraint(
            "date_exited IS NULL OR date_exited >= date_joined",
            name="ck_members_exit_dates",
        ),
        Index("ix_members_status", "status"),
        Index("ix_members_phone", "phone"),
        Index("ix_members_member_number", "member_number"),
        {"schema": "coop"},
    )

    member_number: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_joined: Mapped[date] = mapped_column(Date, nullable=False)
    date_exited: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[MemberStatus] = mapped_column(
        String(20),
        default=MemberStatus.ACTIVE,
        server_default=text("'ACTIVE'"),
        nullable=False,
    )
    exit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("coop.users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relationships
    # Note: passive_deletes=True prevents ORM cascade-deletion of historical share records.
    # Database FK uses ondelete="RESTRICT" to guarantee share records cannot be orphaned.
    shares: Mapped[list["Share"]] = relationship(
        "Share",
        back_populates="member",
        passive_deletes=True,
        order_by="desc(Share.effective_date), desc(Share.created_at)",
        lazy="selectin",
    )
    creator: Mapped["User"] = relationship("User")

    @property
    def current_share_count(self) -> int:
        """Derive the current share count from the latest share history snapshot."""
        if not self.shares or self.status == MemberStatus.EXITED:
            return 0
        latest = max(self.shares, key=_share_sort_key)
        return latest.share_count

    @property
    def current_share_value(self):
        """Derive the current total share valuation from the latest share history snapshot."""
        from decimal import Decimal

        if not self.shares or self.status == MemberStatus.EXITED:
            return Decimal("0.00")
        latest = max(self.shares, key=_share_sort_key)
        return latest.total_value
