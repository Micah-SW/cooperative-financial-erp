"""
Tests for AuthService, Password Hashing, JWT Lifecycle, and Credential Verification.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.enums import AuditAction, UserRole
from app.core.exceptions import AuthenticationError, BusinessValidationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.auth_service import auth_service


def test_password_hashing():
    """Verify bcrypt hashes passwords non-deterministically and verifies correctly."""
    pwd = "SecurePassword123!"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)

    # Hashes must differ due to unique salts
    assert hash1 != hash2
    assert hash1.startswith(("$2b$", "$2a$"))

    # Verification must succeed
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True

    # Bad passwords must fail
    assert verify_password("WrongPassword!", hash1) is False
    assert verify_password("", hash1) is False


def test_jwt_lifecycle_and_claims():
    """Verify access token creation, expiration, and payload parsing."""
    user_id = str(uuid.uuid4())
    token = create_access_token(
        {"sub": user_id, "username": "jwt_user", "role": UserRole.ADMIN},
        expires_delta=timedelta(minutes=15),
    )
    payload = decode_access_token(token)
    assert payload.sub == user_id
    assert payload.username == "jwt_user"
    assert payload.role == UserRole.ADMIN
    assert payload.exp > int(datetime.now(UTC).timestamp())


def test_jwt_expired_token():
    """Verify expired token raises AuthenticationError."""
    user_id = str(uuid.uuid4())
    token = create_access_token(
        {"sub": user_id, "username": "expired_user", "role": UserRole.VIEWER},
        expires_delta=timedelta(seconds=-10),  # expired in past
    )
    with pytest.raises(AuthenticationError) as exc_info:
        decode_access_token(token)
    assert "Could not validate token" in str(exc_info.value)


def test_jwt_tampered_token():
    """Verify tampered token signature raises AuthenticationError."""
    token = create_access_token({"sub": "valid", "username": "user", "role": UserRole.ADMIN})
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(AuthenticationError):
        decode_access_token(tampered)


@pytest.mark.asyncio
async def test_successful_authentication(db_session: AsyncSession, admin_user: User):
    """Verify valid credentials update last_login, return JWT, and log LOGIN audit event."""
    token, user = await auth_service.authenticate(
        db_session,
        username="admin_test",
        password="admin_pass123",
        ip_address="127.0.0.1",
    )
    await db_session.commit()

    assert token is not None
    assert user.id == admin_user.id
    assert user.last_login is not None

    # Verify audit log entry
    stmt = select(AuditLog).where(
        AuditLog.user_id == user.id,
        AuditLog.action == AuditAction.LOGIN.value,
    )
    result = await db_session.execute(stmt)
    entry = result.scalar_one_or_none()
    assert entry is not None
    assert entry.entity_type == "User"
    assert entry.entity_id == user.id
    assert entry.ip_address == "127.0.0.1"


@pytest.mark.asyncio
async def test_incorrect_credentials(db_session: AsyncSession, admin_user: User):
    """Verify bad username or bad password raises AuthenticationError."""
    # Bad username
    with pytest.raises(AuthenticationError) as exc1:
        await auth_service.authenticate(db_session, "non_existent", "admin_pass123")
    assert "Invalid username or password" in str(exc1.value)

    # Bad password
    with pytest.raises(AuthenticationError) as exc2:
        await auth_service.authenticate(db_session, "admin_test", "wrong_password")
    assert "Invalid username or password" in str(exc2.value)


@pytest.mark.asyncio
async def test_disabled_account_rejected(db_session: AsyncSession):
    """Verify disabled user cannot authenticate."""
    disabled_user = User(
        id=uuid.uuid4(),
        username="disabled_user",
        email="disabled@coop.local",
        full_name="Disabled User",
        role=UserRole.VIEWER,
        hashed_password=hash_password("pass12345"),
        is_active=False,
    )
    db_session.add(disabled_user)
    await db_session.commit()

    with pytest.raises(AuthenticationError) as exc:
        await auth_service.authenticate(db_session, "disabled_user", "pass12345")
    assert "inactive" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_password_change_workflow(db_session: AsyncSession, admin_user: User):
    """Verify password change verifies current password, updates hash, and writes audit record."""
    old_hash = admin_user.hashed_password

    # Success case
    await auth_service.change_password(
        db_session,
        user_id=admin_user.id,
        current_password="admin_pass123",
        new_password="NewSecurePassword999!",
    )
    await db_session.commit()
    await db_session.refresh(admin_user)

    assert admin_user.hashed_password != old_hash
    assert verify_password("NewSecurePassword999!", admin_user.hashed_password) is True

    # Audit log check: verify password is not recorded in audit log
    stmt = select(AuditLog).where(
        AuditLog.user_id == admin_user.id,
        AuditLog.action == AuditAction.CONFIG_CHANGE.value,
    )
    result = await db_session.execute(stmt)
    entry = result.scalar_one_or_none()
    assert entry is not None
    assert "new_password" not in entry.new_values
    assert "password" not in entry.new_values

    # Wrong old password
    with pytest.raises(AuthenticationError):
        await auth_service.change_password(
            db_session,
            user_id=admin_user.id,
            current_password="WrongOldPassword",
            new_password="AnotherPassword123!",
        )

    # New password too short (< 8 chars)
    with pytest.raises(BusinessValidationError):
        await auth_service.change_password(
            db_session,
            user_id=admin_user.id,
            current_password="NewSecurePassword999!",
            new_password="short",
        )


def test_jwt_invalid_role_claim():
    """
    Test SEC-04:
    Verify a correctly signed token with an invalid/unsupported role claim
    raises AuthenticationError instead of letting ValueError escape.
    """
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "username": "test_user",
            "role": "UNSUPPORTED_ROLE",
            "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(AuthenticationError, match="Invalid or unsupported role claim"):
        decode_access_token(token)


def test_jwt_missing_required_claims():
    """
    Test SEC-04:
    Verify a correctly signed token missing required claims raises AuthenticationError.
    """
    # Missing role
    token_no_role = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "username": "test_user",
            "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(AuthenticationError, match="missing required claims"):
        decode_access_token(token_no_role)

    # Missing sub
    token_no_sub = jwt.encode(
        {
            "username": "test_user",
            "role": "ADMIN",
            "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(AuthenticationError, match="missing required claims"):
        decode_access_token(token_no_sub)


def test_jwt_malformed_expiration_claim():
    """
    Test SEC-04:
    Verify a token with a non-integer expiration claim raises AuthenticationError.
    """
    token_bad_exp = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "username": "test_user",
            "role": "ADMIN",
            "exp": "not_an_int",
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(AuthenticationError, match="(?i)expiration"):
        decode_access_token(token_bad_exp)

