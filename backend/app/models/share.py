"""
Share ORM Model.

Entity: Share
Schema: coop.shares
Module: Member

See: database_schema.md → coop.shares
See: domain_model.md → Share
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CoopBase

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.user import User


class Share(CoopBase):
    """
    Share allocation and valuation history record.

    Invariants:
        - Share records are append-only snapshots of share state.
        - Share history must be retained across member exit (extinguished with share_count=0).
        - total_value must equal share_count * value_per_share.
    """

    __tablename__ = "shares"
    __table_args__ = (
        CheckConstraint("share_count >= 0", name="ck_shares_count"),
        CheckConstraint("value_per_share > 0", name="ck_shares_value_per_share"),
        CheckConstraint(
            "total_value = (share_count * value_per_share)",
            name="ck_shares_total_value",
        ),
        Index("ix_shares_member_id", "member_id"),
        Index("ix_shares_effective_date", text("effective_date DESC")),
        {"schema": "coop"},
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("coop.members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    share_count: Mapped[int] = mapped_column(Integer, nullable=False)
    value_per_share: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("coop.users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="shares")
    creator: Mapped["User"] = relationship("User")
