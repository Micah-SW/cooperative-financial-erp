"""
Tests for Audit Logging Infrastructure, Event Recording, and Security Redaction.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_service, sanitize_audit_dict
from app.core.enums import AuditAction
from app.models.audit_log import AuditLog
from app.models.user import User


@pytest.mark.asyncio
async def test_audit_log_creation_and_redaction(db_session: AsyncSession, admin_user: User):
    """
    Verify audit logging records event within current transaction
    and automatically sanitizes passwords/tokens.
    """
    test_entity_id = uuid.uuid4()
    entry = await audit_service.log(
        db_session,
        user_id=admin_user.id,
        action=AuditAction.CREATE,
        entity_type="TestEntity",
        entity_id=test_entity_id,
        old_values=None,
        new_values={
            "name": "Audit Test",
            "password": "SecretPassword123!",
            "token": "sensitive_jwt_token_here",
            "safe_field": 42,
        },
        ip_address="192.168.1.100",
    )
    await db_session.commit()

    # Query back the audit log entry
    stmt = select(AuditLog).where(AuditLog.id == entry.id)
    result = await db_session.execute(stmt)
    persisted = result.scalar_one_or_none()

    assert persisted is not None
    assert persisted.user_id == admin_user.id
    assert persisted.action == AuditAction.CREATE.value
    assert persisted.entity_type == "TestEntity"
    assert persisted.entity_id == test_entity_id
    assert persisted.ip_address == "192.168.1.100"

    # CRITICAL: Verify sensitive keys are redacted
    assert persisted.new_values["password"] == "[REDACTED]"
    assert persisted.new_values["token"] == "[REDACTED]"
    assert persisted.new_values["safe_field"] == 42


@pytest.mark.asyncio
async def test_audit_log_transaction_rollback(db_session: AsyncSession, admin_user: User):
    """Verify audit log entry rolls back when parent transaction rolls back."""
    test_entity_id = uuid.uuid4()
    entry = await audit_service.log(
        db_session,
        user_id=admin_user.id,
        action=AuditAction.UPDATE,
        entity_type="RollbackEntity",
        entity_id=test_entity_id,
        new_values={"state": "temporary"},
    )
    await db_session.flush()
    assert entry.id is not None

    # Rollback transaction
    await db_session.rollback()

    # Query back: must NOT exist
    stmt = select(AuditLog).where(AuditLog.entity_id == test_entity_id)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_audit_logs_query_api_filters(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    admin_user: User,
):
    """Verify querying audit logs via API supports filtering by action and entity_type."""
    entity_a = uuid.uuid4()
    entity_b = uuid.uuid4()

    await audit_service.log(
        db_session,
        user_id=admin_user.id,
        action=AuditAction.CONFIG_CHANGE,
        entity_type="SystemConfig",
        entity_id=entity_a,
    )
    await audit_service.log(
        db_session,
        user_id=admin_user.id,
        action=AuditAction.DEACTIVATE,
        entity_type="User",
        entity_id=entity_b,
    )
    await db_session.commit()

    # Filter by action CONFIG_CHANGE
    res1 = await client.get("/api/v1/audit-logs?action=CONFIG_CHANGE", headers=admin_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert all(item["action"] == "CONFIG_CHANGE" for item in data1["items"])
    assert any(item["entity_id"] == str(entity_a) for item in data1["items"])

    # Filter by entity_type User
    res2 = await client.get("/api/v1/audit-logs?entity_type=User", headers=admin_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert all(item["entity_type"] == "User" for item in data2["items"])
    assert any(item["entity_id"] == str(entity_b) for item in data2["items"])


@pytest.mark.asyncio
async def test_user_orm_deletion_cannot_cascade_delete_audit_logs(
    db_session: AsyncSession,
):
    """
    Regression test for SEC-02:
    Verify ORM deletion of a User does NOT cascade-delete associated AuditLog entries.
    Note: In SQLite test harnesses, this verifies passive_deletes behavior and foreign key
    constraints, without claiming to test live PostgreSQL trigger behavior.
    """
    # 1. Create and commit a user
    target_user = User(
        id=uuid.uuid4(),
        username="audit_test_user",
        email="audit_user@coop.local",
        full_name="Audit Target User",
        role="VIEWER",
        hashed_password="some_hashed_password",
        is_active=True,
    )
    db_session.add(target_user)
    await db_session.commit()

    # 2. Record an audit log entry for this user
    audit_entry = await audit_service.log(
        db_session,
        user_id=target_user.id,
        action=AuditAction.CREATE,
        entity_type="User",
        entity_id=target_user.id,
        new_values={"username": target_user.username},
    )
    await db_session.commit()
    audit_id = audit_entry.id

    # 3. Attempt ORM deletion of the user
    await db_session.delete(target_user)

    # 4. Because passive_deletes=True is set, SQLAlchemy does not cascade delete audit_log.
    # The database foreign key restriction prevents orphan deletion or rolls back.
    try:
        await db_session.commit()
    except (IntegrityError, SQLAlchemyError):
        await db_session.rollback()

    # 5. Verify the audit log record was not erased by cascade-delete
    stmt = select(AuditLog).where(AuditLog.id == audit_id)
    result = await db_session.execute(stmt)
    persisted_log = result.scalar_one_or_none()
    assert persisted_log is not None
    assert persisted_log.id == audit_id


def test_nested_structures_sanitization():
    """
    Test SEC-06:
    Verify sanitize_audit_dict recursively redacts sensitive fields
    in nested dictionaries, lists, and tuples.
    """
    sample_data = {
        "user": {
            "name": "Jane Doe",
            "password": "SecretPassword123!",
            "credentials": {
                "token": "bearer-token-value",
                "nested_list": [
                    {"secret": "deep_secret_1", "safe": "public_data"},
                    {"access_token": "deep_token_2"},
                ],
            },
        },
        "tuple_data": (
            {"hashed_password": "$2b$12$abcdef", "label": "auth_tuple"},
            "non_dict_item",
        ),
        "safe_list": [1, 2, "three"],
        "safe_scalar": 42,
    }

    sanitized = sanitize_audit_dict(sample_data)

    # Top-level & nested dicts
    assert sanitized["user"]["name"] == "Jane Doe"
    assert sanitized["user"]["password"] == "[REDACTED]"
    assert sanitized["user"]["credentials"]["token"] == "[REDACTED]"

    # List of dicts
    nested_list = sanitized["user"]["credentials"]["nested_list"]
    assert nested_list[0]["secret"] == "[REDACTED]"
    assert nested_list[0]["safe"] == "public_data"
    assert nested_list[1]["access_token"] == "[REDACTED]"

    # Tuple of dicts
    assert sanitized["tuple_data"][0]["hashed_password"] == "[REDACTED]"
    assert sanitized["tuple_data"][0]["label"] == "auth_tuple"
    assert sanitized["tuple_data"][1] == "non_dict_item"

    # Preserves non-sensitive data
    assert sanitized["safe_list"] == [1, 2, "three"]
    assert sanitized["safe_scalar"] == 42

