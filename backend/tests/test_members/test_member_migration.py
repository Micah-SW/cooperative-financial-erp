"""
Tests for Chapter 04 Alembic migration: head discovery, static SQL generation, and constraint validation.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_chapter_04_migration_discovery():
    """Verify Alembic discovers 20261022_0001 as head with correct lineage."""
    alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"
    config = Config(str(alembic_cfg_path))
    script = ScriptDirectory.from_config(config)

    head = script.get_current_head()
    assert head == "20261022_0001"

    revision = script.get_revision(head)
    assert revision is not None
    assert revision.down_revision == "20261020_0001"
    assert "members and shares" in revision.doc


def test_chapter_04_migration_script_content():
    """Verify Chapter 04 migration script contains required tables, constraints, and indexes."""
    migration_file = (
        Path(__file__).parent.parent.parent
        / "alembic"
        / "versions"
        / "20261022_0001_members_and_shares.py"
    )
    assert migration_file.exists()
    content = migration_file.read_text(encoding="utf-8")

    # Table creation
    assert '"members",' in content
    assert '"shares",' in content

    # Crucial constraints
    assert "ck_members_status" in content
    assert "ck_members_exit_dates" in content
    assert "ck_shares_count" in content
    assert "ck_shares_value_per_share" in content
    assert "ck_shares_total_value" in content

    # Restrictive foreign key deletion to protect share history
    assert 'ondelete="RESTRICT"' in content

    # Indexes
    assert "ix_members_member_number" in content
    assert "ix_members_status" in content
    assert "ix_shares_effective_date" in content
    assert "ix_shares_member_id" in content

    # Downgrade drops
    assert 'op.drop_table("shares"' in content
    assert 'op.drop_table("members"' in content
