"""
Tests for Application Lifecycle, Health, Readiness, and Centralized Error Handling.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_application_metadata():
    """Verify application title, version, and documentation endpoints."""
    assert app.title == settings.APP_NAME
    assert app.version == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Verify liveness probe returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == settings.APP_NAME
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_readiness_endpoint_success(client: AsyncClient):
    """Verify readiness probe returns connected when database is responsive."""
    response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"

    # Also test /readiness alias
    response_alias = await client.get("/readiness")
    assert response_alias.status_code == 200
    assert response_alias.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_not_found_error_envelope(client: AsyncClient, admin_headers: dict[str, str]):
    """Verify NotFoundError produces standard error envelope with 404."""
    # Query non-existent user
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/users/{non_existent_id}", headers=admin_headers)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "NOT_FOUND"
    assert "not found" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_request_validation_error_envelope(client: AsyncClient, admin_headers: dict[str, str]):
    """Verify RequestValidationError produces standard error envelope with 422 and field_errors."""
    # Send empty body to user creation
    response = await client.post("/api/v1/users", json={}, headers=admin_headers)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "VALIDATION_ERROR"
    assert "field_errors" in data["detail"]
    assert len(data["detail"]["field_errors"]) > 0


@pytest.mark.asyncio
async def test_unauthenticated_request_envelope(client: AsyncClient):
    """Verify missing bearer token produces 401 UNAUTHORIZED standard envelope."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_unauthorized_role_request_envelope(client: AsyncClient, viewer_headers: dict[str, str]):
    """Verify insufficient role permissions produces 403 FORBIDDEN standard envelope."""
    response = await client.get("/api/v1/users", headers=viewer_headers)
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_invalid_role_token_returns_401_not_500(client: AsyncClient):
    """
    Test SEC-04:
    Verify sending a signed token with an invalid/unsupported role claim
    returns HTTP 401 UNAUTHORIZED rather than an unhandled 500 error.
    """
    invalid_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "username": "attacker",
            "role": "SUPERUSER_ROLE",
            "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    headers = {"Authorization": f"Bearer {invalid_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "UNAUTHORIZED"
