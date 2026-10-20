"""
Tests for System Configuration Schemas, Service, API, and Effective Dating.
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ConfigValueType
from app.models.system_config import SystemConfig
from app.models.user import User


@pytest.fixture
async def seeded_config(db_session: AsyncSession, admin_user: User) -> SystemConfig:
    """Seed initial configuration entries with effective dates."""
    cfg = SystemConfig(
        id=uuid.uuid4(),
        config_key="SHARE_VALUE",
        config_value="5000.00",
        value_type=ConfigValueType.DECIMAL.value,
        description="Nominal value of one cooperative share in ETB",
        effective_from=date(2026, 1, 1),
        effective_to=None,
        created_by=admin_user.id,
    )
    db_session.add(cfg)

    cfg2 = SystemConfig(
        id=uuid.uuid4(),
        config_key="SHARES_PER_MEMBER",
        config_value="12",
        value_type=ConfigValueType.INTEGER.value,
        description="Number of shares held per member",
        effective_from=date(2026, 1, 1),
        effective_to=None,
        created_by=admin_user.id,
    )
    db_session.add(cfg2)

    await db_session.commit()
    await db_session.refresh(cfg)
    return cfg


@pytest.mark.asyncio
async def test_get_current_config(
    client: AsyncClient,
    admin_headers: dict[str, str],
    seeded_config: SystemConfig,
):
    """Verify listing all active config values returns currently active records."""
    response = await client.get("/api/v1/config", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    keys = [item["config_key"] for item in data]
    assert "SHARE_VALUE" in keys
    assert "SHARES_PER_MEMBER" in keys


@pytest.mark.asyncio
async def test_get_specific_config_key(
    client: AsyncClient,
    admin_headers: dict[str, str],
    seeded_config: SystemConfig,
):
    """Verify reading a specific configuration key."""
    response = await client.get("/api/v1/config/SHARE_VALUE", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["config_key"] == "SHARE_VALUE"
    assert data["config_value"] == "5000.00"
    assert data["value_type"] == "DECIMAL"
    assert data["effective_to"] is None


@pytest.mark.asyncio
async def test_update_config_with_effective_dating(
    client: AsyncClient,
    admin_headers: dict[str, str],
    seeded_config: SystemConfig,
):
    """
    Verify updating a config value closes the old record and creates a new one:
    - old record effective_to = new effective_from - 1 day
    - new record effective_from = new effective_from, effective_to = NULL
    """
    new_effective_date = date(2026, 11, 1)
    payload = {
        "config_value": "6000.00",
        "effective_from": new_effective_date.isoformat(),
        "description": "Share value increased by vote",
    }
    response = await client.put("/api/v1/config/SHARE_VALUE", json=payload, headers=admin_headers)
    assert response.status_code == 200
    new_data = response.json()
    assert new_data["config_value"] == "6000.00"
    assert new_data["effective_from"] == new_effective_date.isoformat()
    assert new_data["effective_to"] is None

    # Query history to verify effective-dating continuity
    history_res = await client.get("/api/v1/config/SHARE_VALUE/history", headers=admin_headers)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data["history"]) == 2

    # Latest record (active)
    latest = history_data["history"][0]
    assert latest["config_value"] == "6000.00"
    assert latest["effective_from"] == "2026-11-01"
    assert latest["effective_to"] is None

    # Previous record (closed)
    previous = history_data["history"][1]
    assert previous["config_value"] == "5000.00"
    assert previous["effective_from"] == "2026-01-01"
    assert previous["effective_to"] == (new_effective_date - timedelta(days=1)).isoformat()


@pytest.mark.asyncio
async def test_config_value_type_validation(
    client: AsyncClient,
    admin_headers: dict[str, str],
    seeded_config: SystemConfig,
):
    """Verify invalid data type rejected with 422 VALIDATION_ERROR."""
    # Invalid decimal
    payload_bad_decimal = {
        "config_value": "not-a-number",
        "effective_from": "2026-12-01",
    }
    res1 = await client.put("/api/v1/config/SHARE_VALUE", json=payload_bad_decimal, headers=admin_headers)
    assert res1.status_code == 422
    assert res1.json()["detail"]["error_code"] == "VALIDATION_ERROR"

    # Invalid integer for SHARES_PER_MEMBER
    payload_bad_int = {
        "config_value": "12.5",
        "effective_from": "2026-12-01",
    }
    res2 = await client.put("/api/v1/config/SHARES_PER_MEMBER", json=payload_bad_int, headers=admin_headers)
    assert res2.status_code == 422
    assert res2.json()["detail"]["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_config_effective_date_validation(
    client: AsyncClient,
    admin_headers: dict[str, str],
    seeded_config: SystemConfig,
):
    """Verify effective date cannot be on or before the current effective date."""
    # Current effective date is 2026-01-01
    payload_past_date = {
        "config_value": "5500.00",
        "effective_from": "2025-12-31",
    }
    res = await client.put("/api/v1/config/SHARE_VALUE", json=payload_past_date, headers=admin_headers)
    assert res.status_code == 422
    assert "must be strictly after" in res.json()["detail"]["message"].lower()
