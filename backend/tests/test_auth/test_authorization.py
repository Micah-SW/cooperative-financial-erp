"""
Tests for Role-Based Authorization and Initial Administrator Bootstrap.
"""

import sys

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import bootstrap_admin, main
from app.core.enums import UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_rbac_user_management_access(
    client: AsyncClient,
    admin_headers: dict[str, str],
    treasurer_headers: dict[str, str],
    viewer_headers: dict[str, str],
):
    """
    Verify RBAC for user management:
    - ADMIN: 200 OK
    - TREASURER: 403 Forbidden
    - VIEWER: 403 Forbidden
    - Unauthenticated: 401 Unauthorized
    """
    # 1. ADMIN can list users
    res_admin = await client.get("/api/v1/users", headers=admin_headers)
    assert res_admin.status_code == 200

    # 2. TREASURER is blocked
    res_treasurer = await client.get("/api/v1/users", headers=treasurer_headers)
    assert res_treasurer.status_code == 403
    assert res_treasurer.json()["detail"]["error_code"] == "FORBIDDEN"

    # 3. VIEWER is blocked
    res_viewer = await client.get("/api/v1/users", headers=viewer_headers)
    assert res_viewer.status_code == 403
    assert res_viewer.json()["detail"]["error_code"] == "FORBIDDEN"

    # 4. Anonymous is rejected
    res_anon = await client.get("/api/v1/users")
    assert res_anon.status_code == 401
    assert res_anon.json()["detail"]["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_rbac_audit_logs_access(
    client: AsyncClient,
    admin_headers: dict[str, str],
    treasurer_headers: dict[str, str],
    viewer_headers: dict[str, str],
):
    """
    Verify RBAC for audit log viewing:
    - ADMIN: 200 OK
    - TREASURER: 403 Forbidden
    - VIEWER: 403 Forbidden
    """
    res_admin = await client.get("/api/v1/audit-logs", headers=admin_headers)
    assert res_admin.status_code == 200

    res_treasurer = await client.get("/api/v1/audit-logs", headers=treasurer_headers)
    assert res_treasurer.status_code == 403

    res_viewer = await client.get("/api/v1/audit-logs", headers=viewer_headers)
    assert res_viewer.status_code == 403


@pytest.mark.asyncio
async def test_rbac_config_endpoints(
    client: AsyncClient,
    admin_headers: dict[str, str],
    treasurer_headers: dict[str, str],
    viewer_headers: dict[str, str],
):
    """
    Verify RBAC for configuration:
    - GET /api/v1/config: ALL roles allowed
    - PUT /api/v1/config/{key}: ADMIN only
    - GET /api/v1/config/{key}/history: ADMIN only
    """
    # All can read config
    assert (await client.get("/api/v1/config", headers=admin_headers)).status_code == 200
    assert (await client.get("/api/v1/config", headers=treasurer_headers)).status_code == 200
    assert (await client.get("/api/v1/config", headers=viewer_headers)).status_code == 200

    # Only admin can view history
    res_hist_viewer = await client.get("/api/v1/config/SHARE_VALUE/history", headers=viewer_headers)
    assert res_hist_viewer.status_code == 403

    res_hist_treasurer = await client.get("/api/v1/config/SHARE_VALUE/history", headers=treasurer_headers)
    assert res_hist_treasurer.status_code == 403

    # Only admin can update
    update_body = {"config_value": "6000.00"}
    res_up_viewer = await client.put("/api/v1/config/SHARE_VALUE", json=update_body, headers=viewer_headers)
    assert res_up_viewer.status_code == 403

    res_up_treasurer = await client.put("/api/v1/config/SHARE_VALUE", json=update_body, headers=treasurer_headers)
    assert res_up_treasurer.status_code == 403


@pytest.mark.asyncio
async def test_bootstrap_admin_mechanism(db_session: AsyncSession):
    """
    Verify safe bootstrap administrator behavior:
    - Creates initial administrator when no admin exists
    - Refuses duplicate initial admin creation
    - Rejects passwords shorter than 8 characters
    """
    # 1. Clean slate check: no admin
    stmt = select(User).where(User.role == UserRole.ADMIN)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None

    # 2. Rejects password < 8 characters
    short_pw_result = await bootstrap_admin(
        username="boot_admin",
        email="boot_admin@coop.local",
        full_name="Bootstrap Admin",
        password="short",
        session=db_session,
    )
    assert short_pw_result is False

    # 3. Successful bootstrap
    created = await bootstrap_admin(
        username="boot_admin",
        email="boot_admin@coop.local",
        full_name="Bootstrap Admin",
        password="ValidBootstrapPassword123!",
        session=db_session,
    )
    assert created is True

    # Verify user in database
    result = await db_session.execute(stmt)
    admin = result.scalar_one_or_none()
    assert admin is not None
    assert admin.username == "boot_admin"
    assert admin.role == UserRole.ADMIN

    # 4. Refuse duplicate bootstrap
    duplicate_attempt = await bootstrap_admin(
        username="second_admin",
        email="second@coop.local",
        full_name="Second Admin",
        password="AnotherPassword123!",
        session=db_session,
    )
    assert duplicate_attempt is False


@pytest.mark.asyncio
async def test_bootstrap_admin_env_var_password(db_session: AsyncSession, monkeypatch):
    """
    Test SEC-03:
    Verify bootstrap_admin reads BOOTSTRAP_ADMIN_PASSWORD environment variable
    when password argument is omitted.
    """
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "EnvPassword12345!")
    created = await bootstrap_admin(
        username="env_boot_admin",
        email="env_boot@coop.local",
        full_name="Env Admin",
        session=db_session,
    )
    assert created is True

    stmt = select(User).where(User.username == "env_boot_admin")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None
    from app.core.security import verify_password
    assert verify_password("EnvPassword12345!", user.hashed_password) is True


def test_bootstrap_cli_rejects_password_flag(monkeypatch):
    """
    Test SEC-03:
    Verify the bootstrap-admin CLI argument parser refuses --password flag,
    preventing secrets from appearing in process tables or shell history.
    """
    monkeypatch.setattr(sys, "argv", ["app.cli", "bootstrap-admin", "--password", "plaintext_secret"])
    with pytest.raises(SystemExit):
        main()


