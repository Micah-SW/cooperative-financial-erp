"""Database migration for members and shares tables.

Revision ID: 20261022_0001
Revises: 20261020_0001
Create Date: 2026-10-22 10:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261022_0001"
down_revision: Union[str, None] = "20261020_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Table: coop.members
    op.create_table(
        "members",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()") if is_postgres else None,
            nullable=False,
        ),
        sa.Column("member_number", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("date_joined", sa.Date(), nullable=False),
        sa.Column("date_exited", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column("exit_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_members"),
        sa.UniqueConstraint("member_number", name="uq_members_member_number"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'EXITED', 'SUSPENDED')",
            name="ck_members_status",
        ),
        sa.CheckConstraint(
            "date_exited IS NULL OR date_exited >= date_joined",
            name="ck_members_exit_dates",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["coop.users.id"],
            ondelete="RESTRICT",
            name="fk_members_created_by_users",
        ),
        schema="coop",
    )
    op.create_index("ix_members_member_number", "members", ["member_number"], unique=False, schema="coop")
    op.create_index("ix_members_phone", "members", ["phone"], unique=False, schema="coop")
    op.create_index("ix_members_status", "members", ["status"], unique=False, schema="coop")

    # 2. Table: coop.shares
    op.create_table(
        "shares",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()") if is_postgres else None,
            nullable=False,
        ),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("share_count", sa.Integer(), nullable=False),
        sa.Column("value_per_share", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("total_value", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_shares"),
        sa.CheckConstraint("share_count >= 0", name="ck_shares_count"),
        sa.CheckConstraint("value_per_share > 0", name="ck_shares_value_per_share"),
        sa.CheckConstraint(
            "total_value = (share_count * value_per_share)",
            name="ck_shares_total_value",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["coop.members.id"],
            ondelete="RESTRICT",
            name="fk_shares_member_id_members",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["coop.users.id"],
            ondelete="RESTRICT",
            name="fk_shares_created_by_users",
        ),
        schema="coop",
    )
    op.create_index("ix_shares_member_id", "shares", ["member_id"], unique=False, schema="coop")
    op.create_index(
        "ix_shares_effective_date",
        "shares",
        [sa.text("effective_date DESC")],
        unique=False,
        schema="coop",
    )


def downgrade() -> None:
    # Drop shares table and indexes
    op.drop_index("ix_shares_effective_date", table_name="shares", schema="coop")
    op.drop_index("ix_shares_member_id", table_name="shares", schema="coop")
    op.drop_table("shares", schema="coop")

    # Drop members table and indexes
    op.drop_index("ix_members_status", table_name="members", schema="coop")
    op.drop_index("ix_members_phone", table_name="members", schema="coop")
    op.drop_index("ix_members_member_number", table_name="members", schema="coop")
    op.drop_table("members", schema="coop")
