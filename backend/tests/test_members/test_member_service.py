"""
Service tests for MemberService: registration, updates, queries, exit lifecycle, and audit logs.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditAction, MemberStatus
from app.core.exceptions import (
    BusinessValidationError,
    DuplicateError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.models.audit_log import AuditLog
from app.models.member import Member
from app.models.system_config import SystemConfig
from app.models.user import User
from app.schemas.member import MemberCreate, MemberExitRequest, MemberUpdate
from app.services.member_service import get_current_shares, member_service


async def _set_config(db_session: AsyncSession, admin_user: User, key: str, value: str, val_type: str = "BOOLEAN"):
    """Helper to seed system configuration values."""
    stmt = select(SystemConfig).where(SystemConfig.config_key == key, SystemConfig.effective_to.is_(None))
    existing = (await db_session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.config_value = value
        existing.value_type = val_type
    else:
        config = SystemConfig(
            id=uuid.uuid4(),
            config_key=key,
            config_value=value,
            value_type=val_type,
            description=f"Test config {key}",
            effective_from=date(2020, 1, 1),
            created_by=admin_user.id,
        )
        db_session.add(config)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_member_fails_when_membership_closed(
    db_session: AsyncSession, admin_user: User
):
    """Verify that registration fails closed if MEMBERSHIP_OPEN is missing or false."""
    data = MemberCreate(
        member_number="M-101",
        full_name="Haile Gebrselassie",
        phone="+251911123456",
        date_joined=date(2024, 1, 10),
    )

    # 1. Config absent -> fails closed
    with pytest.raises(BusinessValidationError, match="Membership is currently closed"):
        await member_service.create_member(db_session, data, admin_user.id)

    # 2. Config explicitly false -> fails closed
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "false")
    with pytest.raises(BusinessValidationError, match="Membership is currently closed"):
        await member_service.create_member(db_session, data, admin_user.id)


@pytest.mark.asyncio
async def test_create_member_success_with_initial_shares_and_audit(
    db_session: AsyncSession, admin_user: User
):
    """Verify successful member creation with initial share allocation and audit logging."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")
    await _set_config(db_session, admin_user, "SHARE_VALUE", "5000.00", "DECIMAL")
    await _set_config(db_session, admin_user, "SHARES_PER_MEMBER", "12", "INTEGER")

    data = MemberCreate(
        member_number="M-201",
        full_name="Derartu Tulu",
        phone="+251911654321",
        email="derartu@example.com",
        address="Arada, Addis Ababa",
        date_joined=date(2024, 2, 1),
        notes="Olympic Champion",
    )

    member = await member_service.create_member(db_session, data, admin_user.id)
    await db_session.commit()

    assert member.member_number == "M-201"
    assert member.status == MemberStatus.ACTIVE
    assert member.current_share_count == 12
    assert member.current_share_value == Decimal("60000.00")
    assert len(member.shares) == 1
    assert member.shares[0].share_count == 12
    assert member.shares[0].value_per_share == Decimal("5000.00")
    assert member.shares[0].total_value == Decimal("60000.00")

    # Verify audit log
    audit_stmt = select(AuditLog).where(
        AuditLog.entity_type == "Member",
        AuditLog.entity_id == member.id,
        AuditLog.action == AuditAction.CREATE.value,
    )
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.user_id == admin_user.id
    assert audit.new_values["member_number"] == "M-201"
    assert audit.new_values["initial_shares"] == 12


@pytest.mark.asyncio
async def test_create_member_duplicate_number_rejected(
    db_session: AsyncSession, admin_user: User
):
    """Verify duplicate member_number raises DuplicateError."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    data = MemberCreate(
        member_number="M-DUP",
        full_name="First Member",
        phone="+251911112233",
        date_joined=date(2024, 1, 1),
    )
    await member_service.create_member(db_session, data, admin_user.id)
    await db_session.commit()

    data2 = MemberCreate(
        member_number="M-DUP",
        full_name="Second Member",
        phone="+251922334455",
        date_joined=date(2024, 1, 2),
    )
    with pytest.raises(DuplicateError, match="M-DUP"):
        await member_service.create_member(db_session, data2, admin_user.id)


@pytest.mark.asyncio
async def test_update_member_mutable_fields_and_audit(
    db_session: AsyncSession, admin_user: User
):
    """Verify updating allowed fields and audit logging."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    member = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-UPD",
            full_name="Original Name",
            phone="+251911000000",
            email="orig@example.com",
            date_joined=date(2024, 1, 1),
        ),
        admin_user.id,
    )
    await db_session.commit()

    # Update phone and email
    update_data = MemberUpdate(
        full_name="Updated Name",
        phone="+251999888777",
        email="updated@example.com",
    )
    updated = await member_service.update_member(db_session, member.id, update_data, admin_user.id)
    await db_session.commit()

    assert updated.full_name == "Updated Name"
    assert updated.phone == "+251999888777"
    assert updated.email == "updated@example.com"
    assert updated.member_number == "M-UPD"

    # Verify audit log
    audit_stmt = select(AuditLog).where(
        AuditLog.entity_type == "Member",
        AuditLog.entity_id == member.id,
        AuditLog.action == AuditAction.UPDATE.value,
    )
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.old_values["full_name"] == "Original Name"
    assert audit.new_values["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_member_rejects_immutable_fields(
    db_session: AsyncSession, admin_user: User
):
    """Verify attempts to modify member_number or status are rejected."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    member = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-IMMUTABLE",
            full_name="Immutable Test",
            phone="+251911555555",
            date_joined=date(2024, 1, 1),
        ),
        admin_user.id,
    )
    await db_session.commit()
    assert member.member_number == "M-IMMUTABLE"

    # Pydantic schema validation rejects immutable fields at input time
    with pytest.raises(ValueError, match="Field 'member_number' is immutable"):
        MemberUpdate.model_validate({"member_number": "M-NEW"})

    with pytest.raises(ValueError, match="Member status cannot be updated directly"):
        MemberUpdate.model_validate({"status": "EXITED"})


@pytest.mark.asyncio
async def test_exit_member_workflow_and_extinguishing_share(
    db_session: AsyncSession, admin_user: User
):
    """
    Verify member exit transitions ACTIVE -> EXITED, appends zero-share record,
    preserves prior history, and writes audit event without financial transactions.
    """
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")
    await _set_config(db_session, admin_user, "SHARE_VALUE", "5000.00", "DECIMAL")

    member = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-EXIT",
            full_name="Abebe Bikila",
            phone="+251911999999",
            date_joined=date(2024, 1, 1),
        ),
        admin_user.id,
    )
    await db_session.commit()

    # Process exit
    exit_data = MemberExitRequest(
        exit_date=date(2024, 7, 1),
        exit_reason="Personal withdrawal from union",
        notes="Administrative approval granted",
    )
    exited = await member_service.exit_member(db_session, member.id, exit_data, admin_user.id)
    await db_session.commit()

    assert exited.status == MemberStatus.EXITED
    assert exited.date_exited == date(2024, 7, 1)
    assert exited.exit_reason == "Personal withdrawal from union"
    assert "[Exit]: Administrative approval granted" in exited.notes

    # Shares: prior share record is preserved, new zero-share record appended
    assert len(exited.shares) == 2
    assert exited.current_share_count == 0
    assert exited.current_share_value == Decimal("0.00")

    # Helper function check
    count, val = get_current_shares(exited)
    assert count == 0
    assert val == Decimal("0.00")

    # Verify audit log
    audit_stmt = select(AuditLog).where(
        AuditLog.entity_type == "Member",
        AuditLog.entity_id == member.id,
        AuditLog.action == AuditAction.EXIT.value,
    )
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.old_values["status"] == MemberStatus.ACTIVE.value
    assert audit.new_values["status"] == MemberStatus.EXITED.value
    assert audit.new_values["current_share_count"] == 0


@pytest.mark.asyncio
async def test_exit_member_invalid_transitions(
    db_session: AsyncSession, admin_user: User
):
    """Verify exiting an already exited member or invalid exit date is rejected."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    member = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-EXIT-INV",
            full_name="Invalid Exit",
            phone="+251911444444",
            date_joined=date(2024, 5, 1),
        ),
        admin_user.id,
    )
    await db_session.commit()

    # Exit date prior to join date -> BusinessValidationError
    with pytest.raises(BusinessValidationError, match="Exit date cannot precede join date"):
        await member_service.exit_member(
            db_session,
            member.id,
            MemberExitRequest(exit_date=date(2024, 4, 30), exit_reason="Too early"),
            admin_user.id,
        )

    # Valid exit
    await member_service.exit_member(
        db_session,
        member.id,
        MemberExitRequest(exit_date=date(2024, 6, 1), exit_reason="Leaving"),
        admin_user.id,
    )
    await db_session.commit()

    # Attempting to exit again -> InvalidStateTransitionError
    with pytest.raises(InvalidStateTransitionError, match="Cannot transition Member"):
        await member_service.exit_member(
            db_session,
            member.id,
            MemberExitRequest(exit_date=date(2024, 7, 1), exit_reason="Again"),
            admin_user.id,
        )


@pytest.mark.asyncio
async def test_list_and_get_members(db_session: AsyncSession, admin_user: User):
    """Verify get_member and list_members with search and filters."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    m1 = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-AAA",
            full_name="Alpha User",
            phone="+251911000001",
            date_joined=date(2024, 1, 1),
        ),
        admin_user.id,
    )
    m2 = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-BBB",
            full_name="Beta User",
            phone="+251911000002",
            date_joined=date(2024, 1, 2),
        ),
        admin_user.id,
    )
    await db_session.commit()

    # get_member
    fetched = await member_service.get_member(db_session, m1.id)
    assert fetched.id == m1.id
    assert fetched.member_number == "M-AAA"

    fetched2 = await member_service.get_member(db_session, m2.id)
    assert fetched2.id == m2.id
    assert fetched2.member_number == "M-BBB"

    # get_member missing -> NotFoundError
    with pytest.raises(NotFoundError):
        await member_service.get_member(db_session, uuid.uuid4())

    # list_members all
    all_members = await member_service.list_members(db_session)
    assert all_members.total >= 2

    # list_members search
    search_res = await member_service.list_members(db_session, search="Alpha")
    assert search_res.total == 1
    assert search_res.items[0].member_number == "M-AAA"

    search_phone = await member_service.list_members(db_session, search="000002")
    assert search_phone.total == 1
    assert search_phone.items[0].member_number == "M-BBB"


@pytest.mark.asyncio
async def test_create_member_flush_duplicate_maps_to_duplicate_error(
    db_session: AsyncSession, admin_user: User
):
    """
    Verify that a genuine duplicate member_number detected during flush
    (e.g. concurrent race) is properly classified as DuplicateError.
    """
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    # Add an uncommitted member directly to the session.
    # Because autoflush=False, the service's pre-query against the database returns None.
    unflushed_member = Member(
        id=uuid.uuid4(),
        member_number="M-FLUSH-RACE",
        full_name="Concurrent Insert",
        phone="+251911777888",
        date_joined=date(2024, 1, 1),
        status=MemberStatus.ACTIVE,
        created_by=admin_user.id,
    )
    db_session.add(unflushed_member)

    # create_member with the same member_number passes the pre-query,
    # but flush hits the uq_members_member_number uniqueness constraint.
    data = MemberCreate(
        member_number="M-FLUSH-RACE",
        full_name="Second Concurrent Insert",
        phone="+251911777889",
        date_joined=date(2024, 1, 2),
    )
    with pytest.raises(DuplicateError, match="M-FLUSH-RACE"):
        await member_service.create_member(db_session, data, admin_user.id)


@pytest.mark.asyncio
async def test_create_member_non_duplicate_integrity_error_preserved(
    db_session: AsyncSession, admin_user: User, monkeypatch
):
    """Verify that a non-duplicate IntegrityError is not misclassified as DuplicateError."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    data = MemberCreate(
        member_number="M-NON-DUP",
        full_name="Non Dup Test",
        phone="+251911888999",
        date_joined=date(2024, 1, 1),
    )

    async def mock_flush(*args, **kwargs):
        raise IntegrityError(
            statement="INSERT INTO coop.members ...",
            params={},
            orig=Exception("FOREIGN KEY constraint failed: fk_members_created_by_users"),
        )

    monkeypatch.setattr(db_session, "flush", mock_flush)

    with pytest.raises(IntegrityError) as exc_info:
        await member_service.create_member(db_session, data, admin_user.id)

    assert not isinstance(exc_info.value, DuplicateError)
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_member_session_state_after_duplicate_error(
    db_session: AsyncSession, admin_user: User
):
    """Verify session remains usable and uncorrupted after a handled duplicate error."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    data1 = MemberCreate(
        member_number="M-STATE-1",
        full_name="First State Member",
        phone="+251911000111",
        date_joined=date(2024, 1, 1),
    )
    m1 = await member_service.create_member(db_session, data1, admin_user.id)
    assert m1.member_number == "M-STATE-1"
    await db_session.commit()

    # Attempt duplicate
    data_dup = MemberCreate(
        member_number="M-STATE-1",
        full_name="Duplicate State Member",
        phone="+251911000222",
        date_joined=date(2024, 1, 2),
    )
    with pytest.raises(DuplicateError):
        await member_service.create_member(db_session, data_dup, admin_user.id)

    # Session is still healthy and can execute queries and commits
    users = (await db_session.execute(select(User))).scalars().all()
    assert len(users) >= 1

    # Can create a non-duplicate member in the same session without rollback errors
    data2 = MemberCreate(
        member_number="M-STATE-2",
        full_name="Second State Member",
        phone="+251911000333",
        date_joined=date(2024, 1, 3),
    )
    m2 = await member_service.create_member(db_session, data2, admin_user.id)
    await db_session.commit()
    assert m2.member_number == "M-STATE-2"


@pytest.mark.asyncio
async def test_create_member_invalid_configuration_values(
    db_session: AsyncSession, admin_user: User
):
    """Verify strictly positive requirements and validation for configured share count and value."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    data = MemberCreate(
        member_number="M-CFG-TEST",
        full_name="Config Validation Test",
        phone="+251911333444",
        date_joined=date(2024, 1, 1),
    )

    # 1. Zero SHARE_VALUE rejected
    await _set_config(db_session, admin_user, "SHARE_VALUE", "0.00", "DECIMAL")
    with pytest.raises(BusinessValidationError, match="SHARE_VALUE must be strictly positive"):
        await member_service.create_member(db_session, data, admin_user.id)

    # 2. Negative SHARE_VALUE rejected
    await _set_config(db_session, admin_user, "SHARE_VALUE", "-5000.00", "DECIMAL")
    with pytest.raises(BusinessValidationError, match="SHARE_VALUE must be strictly positive"):
        await member_service.create_member(db_session, data, admin_user.id)

    # 3. Malformed SHARE_VALUE rejected
    await _set_config(db_session, admin_user, "SHARE_VALUE", "not-a-number", "STRING")
    with pytest.raises(BusinessValidationError, match="Invalid configured SHARE_VALUE"):
        await member_service.create_member(db_session, data, admin_user.id)

    # Reset SHARE_VALUE to valid
    await _set_config(db_session, admin_user, "SHARE_VALUE", "5000.00", "DECIMAL")

    # 4. Zero SHARES_PER_MEMBER rejected
    await _set_config(db_session, admin_user, "SHARES_PER_MEMBER", "0", "INTEGER")
    with pytest.raises(BusinessValidationError, match="SHARES_PER_MEMBER must be strictly positive"):
        await member_service.create_member(db_session, data, admin_user.id)

    # 5. Negative SHARES_PER_MEMBER rejected
    await _set_config(db_session, admin_user, "SHARES_PER_MEMBER", "-12", "INTEGER")
    with pytest.raises(BusinessValidationError, match="SHARES_PER_MEMBER must be strictly positive"):
        await member_service.create_member(db_session, data, admin_user.id)

    # 6. Malformed SHARES_PER_MEMBER rejected
    await _set_config(db_session, admin_user, "SHARES_PER_MEMBER", "twelve", "STRING")
    with pytest.raises(BusinessValidationError, match="Invalid configured SHARES_PER_MEMBER"):
        await member_service.create_member(db_session, data, admin_user.id)


@pytest.mark.asyncio
async def test_exit_member_same_date_as_joined_invariant(
    db_session: AsyncSession, admin_user: User
):
    """
    Verify member exiting on the same date as joining (same effective_date as initial share):
      - Authoritative current share count and value become 0 and 0.00.
      - Previous share record is preserved.
      - Extinguishing share is ordered first deterministically.
    """
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")
    await _set_config(db_session, admin_user, "SHARE_VALUE", "5000.00", "DECIMAL")
    await _set_config(db_session, admin_user, "SHARES_PER_MEMBER", "12", "INTEGER")

    same_date = date(2024, 3, 15)
    member = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-SAME-DATE",
            full_name="Same Date Exit User",
            phone="+251911887766",
            date_joined=same_date,
        ),
        admin_user.id,
    )
    await db_session.commit()

    assert member.current_share_count == 12
    assert member.current_share_value == Decimal("60000.00")
    assert len(member.shares) == 1
    assert member.shares[0].effective_date == same_date

    # Exit on the exact same date
    exit_data = MemberExitRequest(
        exit_date=same_date,
        exit_reason="Immediate departure on join date",
        notes="Same day exit test",
    )
    exited = await member_service.exit_member(db_session, member.id, exit_data, admin_user.id)
    await db_session.commit()

    # Authoritative current share state must be zero
    assert exited.status == MemberStatus.EXITED
    assert exited.date_exited == same_date
    assert exited.current_share_count == 0
    assert exited.current_share_value == Decimal("0.00")

    # get_current_shares helper must also return zero
    count, val = get_current_shares(exited)
    assert count == 0
    assert val == Decimal("0.00")

    # Both share records exist (earlier record preserved)
    assert len(exited.shares) == 2
    # Deterministic ordering: extinguishing record (count=0) is first
    assert exited.shares[0].share_count == 0
    assert exited.shares[0].total_value == Decimal("0.00")
    assert exited.shares[0].effective_date == same_date

    # Earlier share record preserved unchanged
    assert exited.shares[1].share_count == 12
    assert exited.shares[1].total_value == Decimal("60000.00")
    assert exited.shares[1].effective_date == same_date

    # Query afresh via get_member
    fetched = await member_service.get_member(db_session, member.id)
    assert fetched.status == MemberStatus.EXITED
    assert fetched.current_share_count == 0
    assert fetched.current_share_value == Decimal("0.00")
    assert len(fetched.shares) == 2
    assert fetched.shares[0].share_count == 0
    assert fetched.shares[1].share_count == 12


@pytest.mark.asyncio
async def test_exit_member_later_date_invariant(
    db_session: AsyncSession, admin_user: User
):
    """Verify exit on a later date preserves earlier history and sets shares to 0."""
    await _set_config(db_session, admin_user, "MEMBERSHIP_OPEN", "true")

    join_date = date(2024, 1, 1)
    exit_date = date(2024, 6, 30)

    member = await member_service.create_member(
        db_session,
        MemberCreate(
            member_number="M-LATER-DATE",
            full_name="Later Date Exit User",
            phone="+251911998800",
            date_joined=join_date,
        ),
        admin_user.id,
    )
    await db_session.commit()

    exited = await member_service.exit_member(
        db_session,
        member.id,
        MemberExitRequest(exit_date=exit_date, exit_reason="Relocation"),
        admin_user.id,
    )
    await db_session.commit()

    assert exited.status == MemberStatus.EXITED
    assert exited.current_share_count == 0
    assert exited.current_share_value == Decimal("0.00")
    assert len(exited.shares) == 2
    assert exited.shares[0].share_count == 0
    assert exited.shares[0].effective_date == exit_date
    assert exited.shares[1].share_count == 12
    assert exited.shares[1].effective_date == join_date
