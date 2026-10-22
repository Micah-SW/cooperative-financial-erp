"""
Tests for Alembic Migration Configuration, Static SQL Generation, and Foundational Scope.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models.base import CoopBase


def test_migration_files_and_head_revision():
    """Verify that Alembic discovers the migrations chain with Chapter 04 as head."""
    alembic_cfg_path = Path(__file__).parent.parent / "alembic.ini"
    config = Config(str(alembic_cfg_path))
    script = ScriptDirectory.from_config(config)

    # Initial foundation revision
    init_rev = script.get_revision("20261020_0001")
    assert init_rev is not None
    assert init_rev.down_revision is None
    assert "Initial database migration" in init_rev.doc

    # Chapter 04 members and shares revision as current head
    head = script.get_current_head()
    assert head == "20261022_0001"
    ch04_rev = script.get_revision(head)
    assert ch04_rev is not None
    assert ch04_rev.down_revision == "20261020_0001"
    assert "members and shares" in ch04_rev.doc


def test_metadata_contains_only_foundational_and_member_tables():
    """Verify target metadata registers only approved foundational and Chapter 04 member tables."""
    table_keys = set(CoopBase.metadata.tables.keys())
    expected_tables = {
        "coop.users",
        "coop.audit_log",
        "coop.system_config",
        "coop.members",
        "coop.shares",
    }
    assert table_keys == expected_tables

    # Verify no downstream future business tables leaked into metadata
    unwanted = {
        "coop.contributions",
        "coop.withdrawals",
        "coop.transactions",
        "coop.funds",
        "coop.properties",
        "coop.projects",
        "coop.expenses",
    }
    assert table_keys.isdisjoint(unwanted)


def test_migration_script_creates_only_foundational_tables():
    """Verify migration script content explicitly creates only foundational tables."""
    migration_file = (
        Path(__file__).parent.parent
        / "alembic"
        / "versions"
        / "20261020_0001_initial_foundations.py"
    )
    assert migration_file.exists()
    content = migration_file.read_text(encoding="utf-8")

    assert 'op.create_table(\n        "users"' in content or 'op.create_table("users"' in content or '"users",' in content
    assert '"audit_log",' in content
    assert '"system_config",' in content

    # Check for unwanted tables
    for business_table in ["members", "shares", "contributions", "withdrawals", "transactions", "funds"]:
        assert f'op.create_table("{business_table}"' not in content
        assert f'op.create_table(\n        "{business_table}"' not in content


def test_do_run_migrations_transaction_boundaries():
    """Verify that do_run_migrations explicitly commits schema creation in its own transaction

    when not already in transaction on PostgreSQL, while preserving external transactions and SQLite.
    """
    import importlib.util
    from unittest.mock import MagicMock, patch

    from sqlalchemy.dialects import postgresql, sqlite

    from alembic import context

    alembic_cfg_path = Path(__file__).parent.parent / "alembic.ini"
    config = Config(str(alembic_cfg_path))
    context.config = config

    with (
        patch.object(context, "is_offline_mode", return_value=True),
        patch.object(context, "configure"),
        patch.object(context, "begin_transaction"),
        patch.object(context, "run_migrations"),
    ):
        spec = importlib.util.spec_from_file_location(
            "alembic_env_unit_test",
            str(Path(__file__).parent.parent / "alembic" / "env.py"),
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

    # 1. PostgreSQL connection not in transaction -> calls connection.begin()
    mock_conn_pg = MagicMock()
    mock_conn_pg.dialect = postgresql.dialect()
    mock_conn_pg.in_transaction.return_value = False
    tx_mgr = MagicMock()
    mock_conn_pg.begin.return_value = tx_mgr

    with (
        patch.object(context, "configure") as mock_cfg,
        patch.object(context, "begin_transaction"),
        patch.object(context, "run_migrations"),
    ):
        mod.do_run_migrations(mock_conn_pg)
        mock_conn_pg.begin.assert_called_once()
        mock_conn_pg.execute.assert_called_once()
        mock_cfg.assert_called_once()
        assert mock_cfg.call_args[1]["version_table_schema"] == "coop"

    # 2. PostgreSQL connection already in transaction -> does NOT call connection.begin()
    mock_conn_pg_tx = MagicMock()
    mock_conn_pg_tx.dialect = postgresql.dialect()
    mock_conn_pg_tx.in_transaction.return_value = True

    with (
        patch.object(context, "configure") as mock_cfg,
        patch.object(context, "begin_transaction"),
        patch.object(context, "run_migrations"),
    ):
        mod.do_run_migrations(mock_conn_pg_tx)
        mock_conn_pg_tx.begin.assert_not_called()
        mock_conn_pg_tx.execute.assert_called_once()
        mock_cfg.assert_called_once()
        assert mock_cfg.call_args[1]["version_table_schema"] == "coop"

    # 3. SQLite dialect -> does not execute schema creation and version_table_schema is None
    mock_conn_sq = MagicMock()
    mock_conn_sq.dialect = sqlite.dialect()
    mock_conn_sq.in_transaction.return_value = False

    with (
        patch.object(context, "configure") as mock_cfg,
        patch.object(context, "begin_transaction"),
        patch.object(context, "run_migrations"),
    ):
        mod.do_run_migrations(mock_conn_sq)
        mock_conn_sq.begin.assert_not_called()
        mock_conn_sq.execute.assert_not_called()
        mock_cfg.assert_called_once()
        assert mock_cfg.call_args[1]["version_table_schema"] is None
