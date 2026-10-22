"""
Unit tests for Member and Share ORM Models, constraints, and relationships.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemberStatus
from app.models.member import Member
from app.models.share import Share
from app.models.user import User


@pytest.mark.asyncio
async def test_member_creation_and_defaults(db_session: AsyncSession, admin_user: User):
    """Verify Member model defaults, fields, and creator FK."""
    member = Member(
        id=uuid.uuid4(),
        member_number="MEM-001",
        full_name="Almaz Ayana",
        phone="+251911223344",
        email="almaz@example.com",
        address="Bole, Addis Ababa",
        date_joined=date(2024, 1, 15),
        created_by=admin_user.id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    assert member.member_number == "MEM-001"
    assert member.full_name == "Almaz Ayana"
    assert member.status == MemberStatus.ACTIVE
    assert member.date_exited is None
    assert member.exit_reason is None
    assert member.created_at is not None
    assert member.updated_at is None
    assert member.created_by == admin_user.id
    assert member.current_share_count == 0
    assert member.current_share_value == Decimal("0.00")


@pytest.mark.asyncio
async def test_member_unique_member_number(db_session: AsyncSession, admin_user: User):
    """Verify uniqueness constraint on member_number."""
    m1 = Member(
        id=uuid.uuid4(),
        member_number="MEM-DUP",
        full_name="Member One",
        phone="+251911111111",
        date_joined=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(m1)
    await db_session.commit()

    m2 = Member(
        id=uuid.uuid4(),
        member_number="MEM-DUP",
        full_name="Member Two",
        phone="+251922222222",
        date_joined=date(2024, 1, 2),
        created_by=admin_user.id,
    )
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_member_exit_date_constraint(db_session: AsyncSession, admin_user: User):
    """Verify check constraint preventing date_exited < date_joined."""
    m = Member(
        id=uuid.uuid4(),
        member_number="MEM-INVALID-DATE",
        full_name="Invalid Date",
        phone="+251911333333",
        date_joined=date(2024, 5, 1),
        date_exited=date(2024, 4, 30),  # Prior to join date
        status=MemberStatus.EXITED,
        created_by=admin_user.id,
    )
    db_session.add(m)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_share_creation_and_arithmetic_constraint(
    db_session: AsyncSession, admin_user: User
):
    """Verify Share model fields, constraints, and total_value arithmetic."""
    member = Member(
        id=uuid.uuid4(),
        member_number="MEM-SHARE-01",
        full_name="Kenenisa Bekele",
        phone="+251911445566",
        date_joined=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(member)
    await db_session.commit()

    # Valid share creation (12 * 5,000 = 60,000)
    share = Share(
        id=uuid.uuid4(),
        member_id=member.id,
        share_count=12,
        value_per_share=Decimal("5000.00"),
        total_value=Decimal("60000.00"),
        effective_date=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(member)

    assert member.current_share_count == 12
    assert member.current_share_value == Decimal("60000.00")
    assert len(member.shares) == 1

    # Invalid share creation: total_value mismatch
    bad_share = Share(
        id=uuid.uuid4(),
        member_id=member.id,
        share_count=10,
        value_per_share=Decimal("5000.00"),
        total_value=Decimal("40000.00"),  # Should be 50,000
        effective_date=date(2024, 2, 1),
        created_by=admin_user.id,
    )
    db_session.add(bad_share)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_share_count_negative_rejected(db_session: AsyncSession, admin_user: User):
    """Verify check constraint rejecting negative share count."""
    member = Member(
        id=uuid.uuid4(),
        member_number="MEM-NEG-SHARE",
        full_name="Negative Share",
        phone="+251911778899",
        date_joined=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(member)
    await db_session.commit()

    bad_share = Share(
        id=uuid.uuid4(),
        member_id=member.id,
        share_count=-1,
        value_per_share=Decimal("5000.00"),
        total_value=Decimal("-5000.00"),
        effective_date=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(bad_share)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_multiple_shares_history_persistence_and_ordering(
    db_session: AsyncSession, admin_user: User
):
    """Verify share history retention, extinguishing record, and deterministic ordering."""
    member = Member(
        id=uuid.uuid4(),
        member_number="MEM-HIST-01",
        full_name="Tirunesh Dibaba",
        phone="+251911998877",
        date_joined=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(member)
    await db_session.commit()

    # Initial 12 shares on 2024-01-01
    s1 = Share(
        id=uuid.uuid4(),
        member_id=member.id,
        share_count=12,
        value_per_share=Decimal("5000.00"),
        total_value=Decimal("60000.00"),
        effective_date=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(s1)
    await db_session.commit()

    # Exit extinguishing record on 2024-06-30
    s2 = Share(
        id=uuid.uuid4(),
        member_id=member.id,
        share_count=0,
        value_per_share=Decimal("5000.00"),
        total_value=Decimal("0.00"),
        effective_date=date(2024, 6, 30),
        created_by=admin_user.id,
    )
    db_session.add(s2)
    member.status = MemberStatus.EXITED
    member.date_exited = date(2024, 6, 30)
    member.exit_reason = "Relocated abroad"
    await db_session.commit()

    # Reload fresh from database
    result = await db_session.execute(select(Member).where(Member.id == member.id))
    reloaded = result.scalar_one()

    # Verify both records persist
    assert len(reloaded.shares) == 2
    # First in list should be newest (2024-06-30)
    assert reloaded.shares[0].share_count == 0
    assert reloaded.shares[0].total_value == Decimal("0.00")
    assert reloaded.shares[1].share_count == 12
    assert reloaded.shares[1].total_value == Decimal("60000.00")

    # Current share state properties should report 0 and 0.00
    assert reloaded.current_share_count == 0
    assert reloaded.current_share_value == Decimal("0.00")


@pytest.mark.asyncio
async def test_member_deletion_does_not_cascade_delete_shares(
    db_session: AsyncSession, admin_user: User
):
    """
    Verify ORM relationship prevents cascade deletion of share history.

    Confirms passive_deletes=True and that Share records are not automatically orphan-deleted.
    """
    member = Member(
        id=uuid.uuid4(),
        member_number="MEM-NOCASCADE",
        full_name="No Cascade Member",
        phone="+251912345678",
        date_joined=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(member)
    await db_session.commit()

    share = Share(
        id=uuid.uuid4(),
        member_id=member.id,
        share_count=12,
        value_per_share=Decimal("5000.00"),
        total_value=Decimal("60000.00"),
        effective_date=date(2024, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(share)
    await db_session.commit()

    # Confirm relationship configuration
    rel = Member.__mapper__.relationships["shares"]
    assert rel.cascade.delete_orphan is False
    assert rel.cascade.delete is False
    assert rel.passive_deletes is True
