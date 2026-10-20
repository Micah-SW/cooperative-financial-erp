"""Initial database migration for foundational tables.

Revision ID: 20261020_0001
Revises: None
Create Date: 2026-10-20 11:35:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261020_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure coop schema and pgcrypto extension exist in PostgreSQL
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("CREATE SCHEMA IF NOT EXISTS coop")
        op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 2. Table: coop.users
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()") if is_postgres else None,
            nullable=False,
        ),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "role IN ('ADMIN', 'TREASURER', 'VIEWER')",
            name="ck_users_role",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        schema="coop",
    )
    op.create_index("ix_users_role", "users", ["role"], unique=False, schema="coop")

    # 3. Table: coop.audit_log
    json_col = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()") if is_postgres else None,
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("old_values", json_col, nullable=True),
        sa.Column("new_values", json_col, nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'VERIFY', 'REVERSE', 'APPROVE', "
            "'REJECT', 'EXIT', 'DEACTIVATE', 'LOGIN', 'CONFIG_CHANGE')",
            name="ck_audit_log_action",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["coop.users.id"],
            name="fk_audit_log_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        schema="coop",
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"], unique=False, schema="coop")
    op.create_index("ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"], unique=False, schema="coop")
    op.create_index(
        "ix_audit_log_created_at",
        "audit_log",
        [sa.text("created_at DESC")],
        unique=False,
        schema="coop",
    )

    # 4. Table: coop.system_config
    op.create_table(
        "system_config",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()") if is_postgres else None,
            nullable=False,
        ),
        sa.Column("config_key", sa.String(length=50), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "value_type IN ('DECIMAL', 'INTEGER', 'STRING', 'BOOLEAN')",
            name="ck_system_config_value_type",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_system_config_dates",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["coop.users.id"],
            name="fk_system_config_created_by_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_system_config"),
        sa.UniqueConstraint("config_key", "effective_from", name="uq_system_config_key_effective"),
        schema="coop",
    )
    op.create_index(
        "ix_system_config_lookup",
        "system_config",
        ["config_key", "effective_from", "effective_to"],
        unique=False,
        schema="coop",
    )

    # 5. Immutability trigger on audit_log in PostgreSQL
    if is_postgres:
        op.execute("""
            CREATE OR REPLACE FUNCTION coop.prevent_ledger_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'Immutability violation: records in %.% cannot be updated or deleted.',
                    TG_TABLE_SCHEMA, TG_TABLE_NAME
                    USING ERRCODE = 'restrict_violation';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER trg_immutable_audit_log
                BEFORE UPDATE OR DELETE ON coop.audit_log
                FOR EACH ROW EXECUTE FUNCTION coop.prevent_ledger_mutation();
        """)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("DROP TRIGGER IF EXISTS trg_immutable_audit_log ON coop.audit_log")
        op.execute("DROP FUNCTION IF EXISTS coop.prevent_ledger_mutation()")

    op.drop_index("ix_system_config_lookup", table_name="system_config", schema="coop")
    op.drop_table("system_config", schema="coop")

    op.drop_index("ix_audit_log_created_at", table_name="audit_log", schema="coop")
    op.drop_index("ix_audit_log_entity", table_name="audit_log", schema="coop")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log", schema="coop")
    op.drop_table("audit_log", schema="coop")

    op.drop_index("ix_users_role", table_name="users", schema="coop")
    op.drop_table("users", schema="coop")

    if is_postgres:
        op.execute("DROP SCHEMA IF EXISTS coop CASCADE")
