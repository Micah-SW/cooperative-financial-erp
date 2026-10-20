"""
Tests for User Administration, Creation, Modification, and Deactivation.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.enums import UserRole
from app.core.exceptions import BusinessValidationError
from app.schemas.user import UserUpdate
from app.services.auth_service import auth_service


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, admin_headers: dict[str, str]):
    """Verify administrator can create a new user with secure password hashing."""
    payload = {
        "username": "new_treasurer",
        "email": "treasurer_new@coop.local",
        "full_name": "New Treasurer",
        "role": UserRole.TREASURER.value,
        "password": "StrongPassword123!",
    }
    response = await client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()

    assert data["username"] == "new_treasurer"
    assert data["email"] == "treasurer_new@coop.local"
    assert data["role"] == UserRole.TREASURER.value
    assert data["is_active"] is True
    assert "id" in data

    # CRITICAL: Verify password hash or password is NEVER exposed in the response
    assert "password" not in data
    assert "hashed_password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient, admin_headers: dict[str, str]):
    """Verify duplicate username is rejected with 409 DUPLICATE."""
    payload = {
        "username": "duplicate_user",
        "email": "unique1@coop.local",
        "full_name": "User One",
        "role": UserRole.VIEWER.value,
        "password": "Password123!",
    }
    res1 = await client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert res1.status_code == 201

    payload["email"] = "unique2@coop.local"
    res2 = await client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert res2.status_code == 409
    assert res2.json()["detail"]["error_code"] == "DUPLICATE"


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, admin_headers: dict[str, str]):
    """Verify duplicate email is rejected with 409 DUPLICATE."""
    payload1 = {
        "username": "user_a",
        "email": "same_email@coop.local",
        "full_name": "User A",
        "role": UserRole.VIEWER.value,
        "password": "Password123!",
    }
    res1 = await client.post("/api/v1/users", json=payload1, headers=admin_headers)
    assert res1.status_code == 201

    payload2 = {
        "username": "user_b",
        "email": "same_email@coop.local",
        "full_name": "User B",
        "role": UserRole.VIEWER.value,
        "password": "Password123!",
    }
    res2 = await client.post("/api/v1/users", json=payload2, headers=admin_headers)
    assert res2.status_code == 409
    assert res2.json()["detail"]["error_code"] == "DUPLICATE"


@pytest.mark.asyncio
async def test_list_and_get_users(client: AsyncClient, admin_headers: dict[str, str]):
    """Verify user list is paginated and user details can be fetched."""
    response = await client.get("/api/v1/users?page=1&per_page=10", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["per_page"] == 10
    assert len(data["items"]) >= 1

    first_user_id = data["items"][0]["id"]
    get_res = await client.get(f"/api/v1/users/{first_user_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == first_user_id


@pytest.mark.asyncio
async def test_update_and_deactivate_user(client: AsyncClient, admin_headers: dict[str, str]):
    """Verify modifying user details and deactivating user account."""
    # Create user to update
    payload = {
        "username": "user_to_edit",
        "email": "edit_me@coop.local",
        "full_name": "Before Edit",
        "role": UserRole.VIEWER.value,
        "password": "Password123!",
    }
    res = await client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert res.status_code == 201
    user_id = res.json()["id"]

    # Update full_name and role
    update_payload = {
        "full_name": "After Edit",
        "role": UserRole.TREASURER.value,
    }
    patch_res = await client.patch(f"/api/v1/users/{user_id}", json=update_payload, headers=admin_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["full_name"] == "After Edit"
    assert patch_res.json()["role"] == UserRole.TREASURER.value

    # Deactivate user
    deact_res = await client.post(f"/api/v1/users/{user_id}/deactivate", headers=admin_headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_self(
    client: AsyncClient,
    admin_user,
    admin_headers: dict[str, str],
):
    """Verify administrator cannot deactivate their own account via endpoint."""
    res = await client.post(
        f"/api/v1/users/{admin_user.id}/deactivate",
        headers=admin_headers,
    )
    assert res.status_code == 422
    assert "cannot deactivate their own account" in res.json()["detail"]["message"].lower()

    # Also test via PATCH is_active: false
    patch_res = await client.patch(
        f"/api/v1/users/{admin_user.id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert patch_res.status_code == 422
    assert "cannot deactivate their own account" in patch_res.json()["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_admin_cannot_demote_self(
    client: AsyncClient,
    admin_user,
    admin_headers: dict[str, str],
):
    """Verify administrator cannot demote their own account to VIEWER or TREASURER."""
    res = await client.patch(
        f"/api/v1/users/{admin_user.id}",
        json={"role": UserRole.VIEWER.value},
        headers=admin_headers,
    )
    assert res.status_code == 422
    assert "cannot demote their own account" in res.json()["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_admin_can_make_unrelated_edits_to_self(
    client: AsyncClient,
    admin_user,
    admin_headers: dict[str, str],
):
    """Verify administrator can update own display name, email, or keep role as ADMIN."""
    res = await client.patch(
        f"/api/v1/users/{admin_user.id}",
        json={"full_name": "Updated Admin Name", "role": UserRole.ADMIN.value},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["full_name"] == "Updated Admin Name"
    assert res.json()["role"] == UserRole.ADMIN.value


@pytest.mark.asyncio
async def test_cannot_demote_or_deactivate_sole_active_admin(
    client: AsyncClient,
    admin_user,
    admin_headers: dict[str, str],
    db_session,
):
    """Verify that when only one admin exists, deactivating or demoting is prohibited."""
    # Create second admin
    admin2_payload = {
        "username": "second_admin_test",
        "email": "admin2_test@coop.local",
        "full_name": "Second Admin",
        "role": UserRole.ADMIN.value,
        "password": "Password123!",
    }
    create_res = await client.post("/api/v1/users", json=admin2_payload, headers=admin_headers)
    assert create_res.status_code == 201
    admin2_id = create_res.json()["id"]

    # With 2 active admins, demoting admin2 succeeds
    demote_res = await client.patch(
        f"/api/v1/users/{admin2_id}",
        json={"role": UserRole.TREASURER.value},
        headers=admin_headers,
    )
    assert demote_res.status_code == 200
    assert demote_res.json()["role"] == UserRole.TREASURER.value

    # Now admin_user is the sole remaining active admin.
    # Simulate another actor trying to demote the sole admin:
    fake_actor_id = uuid.uuid4()
    with pytest.raises(BusinessValidationError, match="sole remaining active administrator"):
        await auth_service.update_user(
            db_session,
            user_id=admin_user.id,
            data=UserUpdate(role=UserRole.VIEWER),
            actor_id=fake_actor_id,
        )

    # Simulate another actor trying to deactivate the sole admin:
    with pytest.raises(BusinessValidationError, match="sole remaining active administrator"):
        await auth_service.deactivate_user(
            db_session,
            user_id=admin_user.id,
            actor_id=fake_actor_id,
        )

