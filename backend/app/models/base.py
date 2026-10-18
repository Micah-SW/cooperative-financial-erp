"""
Base model with standard audit columns.

All domain models MUST inherit from CoopBase.
This ensures consistent:
  - UUID primary keys
  - created_at timestamps
  - Schema targeting (coop schema)

Models that track mutations should also include updated_at.
Models that track authorship should include created_by (FK to users).

IMPLEMENTATION NOTE:
  - Use SQLAlchemy 2.0 Mapped[] style
  - Use server_default for timestamps, not Python-side defaults
  - All monetary fields: Numeric(15, 2)
  - All tables target schema='coop'
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, Uuid, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class CoopBase(DeclarativeBase):
    """Abstract base with UUID PK and created_at timestamp in coop schema."""

    __abstract__ = True
    metadata = MetaData(schema="coop", naming_convention=naming_convention)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
