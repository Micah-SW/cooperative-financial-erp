"""
Tests for Alembic Migration Configuration, Static SQL Generation, and Foundational Scope.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models.base import CoopBase


def test_migration_files_and_head_revision():
    """Verify that Alembic discovers the initial foundation migration as head."""
    alembic_cfg_path = Path(__file__).parent.parent / "alembic.ini"
    config = Config(str(alembic_cfg_path))
    script = ScriptDirectory.from_config(config)

    head = script.get_current_head()
    assert head == "20261020_0001"

    revision = script.get_revision(head)
    assert revision is not None
    assert revision.down_revision is None
    assert "Initial database migration" in revision.doc


def test_metadata_contains_only_foundational_tables():
    """Verify target metadata registers only the approved foundational tables."""
    table_keys = set(CoopBase.metadata.tables.keys())
    expected_foundational_tables = {
        "coop.users",
        "coop.audit_log",
        "coop.system_config",
    }
    assert table_keys == expected_foundational_tables

    # Verify no unfinished business tables leaked into metadata
    unwanted = {
        "coop.members",
        "coop.shares",
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
