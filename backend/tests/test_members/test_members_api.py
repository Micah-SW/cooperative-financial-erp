"""
API endpoint and RBAC authorization tests for the Members domain (/api/v1/members).
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig
from app.models.user import User


async def _open_membership(db_session: AsyncSession, admin_user: User):
    """Seed MEMBERSHIP_OPEN=true and default share settings."""
    cfg = SystemConfig(
        id=uuid.uuid4(),
        config_key="MEMBERSHIP_OPEN",
        config_value="true",
        value_type="BOOLEAN",
        description="Allow membership registration",
        effective_from=date(2020, 1, 1),
        created_by=admin_user.id,
    )
    db_session.add(cfg)
    await db_session.commit()


@pytest.mark.asyncio
async def test_admin_can_create_member(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
):
    """Verify administrator can register a new member."""
    await _open_membership(db_session, admin_user)

    payload = {
        "member_number": "MEM-API-01",
        "full_name": "Meseret Defar",
        "phone": "+251911333444",
        "email": "meseret@example.com",
        "address": "Kirkos, Addis Ababa",
        "date_joined": "2024-03-01",
        "notes": "Olympic gold medalist",
    }
    response = await client.post("/api/v1/members", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["member_number"] == "MEM-API-01"
    assert data["full_name"] == "Meseret Defar"
    assert data["status"] == "ACTIVE"
    assert data["current_share_count"] == 12
    assert data["current_share_value"] == "60000.00"
    assert len(data["shares"]) == 1
    assert data["shares"][0]["share_count"] == 12


@pytest.mark.asyncio
async def test_treasurer_and_viewer_cannot_create_member(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    treasurer_headers: dict[str, str],
    viewer_headers: dict[str, str],
):
    """Verify non-admin roles receive 403 Forbidden on create."""
    await _open_membership(db_session, admin_user)

    payload = {
        "member_number": "MEM-DENIED",
        "full_name": "Denied Member",
        "phone": "+251911000111",
        "date_joined": "2024-01-01",
    }

    # Treasurer -> 403
    t_res = await client.post("/api/v1/members", json=payload, headers=treasurer_headers)
    assert t_res.status_code == 403
    assert t_res.json()["detail"]["error_code"] == "FORBIDDEN"

    # Viewer -> 403
    v_res = await client.post("/api/v1/members", json=payload, headers=viewer_headers)
    assert v_res.status_code == 403
    assert v_res.json()["detail"]["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_closed_membership_rejected_via_api(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    """Verify registration request fails with 422 when membership is closed."""
    payload = {
        "member_number": "MEM-CLOSED",
        "full_name": "Closed Registration",
        "phone": "+251911222333",
        "date_joined": "2024-01-01",
    }
    response = await client.post("/api/v1/members", json=payload, headers=admin_headers)
    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "VALIDATION_ERROR"
    assert "Membership is currently closed" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_duplicate_member_number_returns_409(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
):
    """Verify duplicate member number returns HTTP 409 DUPLICATE error envelope."""
    await _open_membership(db_session, admin_user)

    payload = {
        "member_number": "MEM-UNIQUE-DUP",
        "full_name": "First Creation",
        "phone": "+251911333555",
        "date_joined": "2024-01-01",
    }
    res1 = await client.post("/api/v1/members", json=payload, headers=admin_headers)
    assert res1.status_code == 201

    payload2 = {
        "member_number": "MEM-UNIQUE-DUP",
        "full_name": "Second Creation Attempt",
        "phone": "+251911333777",
        "date_joined": "2024-01-02",
    }
    res2 = await client.post("/api/v1/members", json=payload2, headers=admin_headers)
    assert res2.status_code == 409
    assert res2.json()["detail"]["error_code"] == "DUPLICATE"


@pytest.mark.asyncio
async def test_all_roles_can_list_and_read_members(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
    treasurer_headers: dict[str, str],
    viewer_headers: dict[str, str],
):
    """Verify ADMIN, TREASURER, and VIEWER can list and view member profiles."""
    await _open_membership(db_session, admin_user)

    create_res = await client.post(
        "/api/v1/members",
        json={
            "member_number": "MEM-READ-TEST",
            "full_name": "Read Test User",
            "phone": "+251911888999",
            "date_joined": "2024-01-01",
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    member_id = create_res.json()["id"]

    # 1. Admin reads
    res_admin = await client.get("/api/v1/members", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["total"] >= 1

    # 2. Treasurer reads
    res_treasurer = await client.get("/api/v1/members", headers=treasurer_headers)
    assert res_treasurer.status_code == 200

    detail_t = await client.get(f"/api/v1/members/{member_id}", headers=treasurer_headers)
    assert detail_t.status_code == 200
    assert detail_t.json()["member_number"] == "MEM-READ-TEST"

    # 3. Viewer reads
    res_viewer = await client.get("/api/v1/members", headers=viewer_headers)
    assert res_viewer.status_code == 200

    detail_v = await client.get(f"/api/v1/members/{member_id}", headers=viewer_headers)
    assert detail_v.status_code == 200
    assert detail_v.json()["full_name"] == "Read Test User"


@pytest.mark.asyncio
async def test_admin_update_and_immutability_guards(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
    treasurer_headers: dict[str, str],
):
    """Verify update endpoint allows mutable fields and rejects immutable fields."""
    await _open_membership(db_session, admin_user)

    create_res = await client.post(
        "/api/v1/members",
        json={
            "member_number": "MEM-UP-API",
            "full_name": "Before Update",
            "phone": "+251911122233",
            "date_joined": "2024-01-01",
        },
        headers=admin_headers,
    )
    member_id = create_res.json()["id"]

    # Valid update by Admin
    up_res = await client.put(
        f"/api/v1/members/{member_id}",
        json={"full_name": "After Update", "phone": "+251999111222"},
        headers=admin_headers,
    )
    assert up_res.status_code == 200
    assert up_res.json()["full_name"] == "After Update"
    assert up_res.json()["phone"] == "+251999111222"

    # Immutable member_number update rejected
    bad_res1 = await client.put(
        f"/api/v1/members/{member_id}",
        json={"member_number": "NEW-NUM"},
        headers=admin_headers,
    )
    assert bad_res1.status_code == 422
    assert bad_res1.json()["detail"]["error_code"] == "VALIDATION_ERROR"

    # Immutable status update rejected
    bad_res2 = await client.put(
        f"/api/v1/members/{member_id}",
        json={"status": "EXITED"},
        headers=admin_headers,
    )
    assert bad_res2.status_code == 422

    # Treasurer update forbidden
    t_res = await client.put(
        f"/api/v1/members/{member_id}",
        json={"full_name": "Treasurer Try"},
        headers=treasurer_headers,
    )
    assert t_res.status_code == 403


@pytest.mark.asyncio
async def test_admin_exit_member_workflow_api(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
    viewer_headers: dict[str, str],
):
    """Verify admin can process member exit and non-admin is forbidden."""
    await _open_membership(db_session, admin_user)

    create_res = await client.post(
        "/api/v1/members",
        json={
            "member_number": "MEM-EXIT-API",
            "full_name": "Exit API User",
            "phone": "+251911444555",
            "date_joined": "2024-01-01",
        },
        headers=admin_headers,
    )
    member_id = create_res.json()["id"]

    # Viewer attempt -> 403 Forbidden
    v_res = await client.post(
        f"/api/v1/members/{member_id}/exit",
        json={"exit_date": "2024-06-01", "exit_reason": "Viewer try"},
        headers=viewer_headers,
    )
    assert v_res.status_code == 403

    # Admin exit -> 200 OK
    exit_res = await client.post(
        f"/api/v1/members/{member_id}/exit",
        json={"exit_date": "2024-06-01", "exit_reason": "Authorized exit"},
        headers=admin_headers,
    )
    assert exit_res.status_code == 200
    exit_data = exit_res.json()
    assert exit_data["status"] == "EXITED"
    assert exit_data["date_exited"] == "2024-06-01"
    assert exit_data["current_share_count"] == 0
    assert exit_data["current_share_value"] == "0.00"
    assert len(exit_data["shares"]) == 2


@pytest.mark.asyncio
async def test_pagination_and_search_api(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
):
    """Verify pagination and query filters on /api/v1/members."""
    await _open_membership(db_session, admin_user)

    for i in range(1, 4):
        await client.post(
            "/api/v1/members",
            json={
                "member_number": f"MEM-PAGE-{i:02d}",
                "full_name": f"Page Tester {i}",
                "phone": f"+2519110000{i:02d}",
                "date_joined": "2024-01-01",
            },
            headers=admin_headers,
        )

    # Paging test
    paged = await client.get("/api/v1/members?page=1&per_page=2", headers=admin_headers)
    assert paged.status_code == 200
    data = paged.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total"] >= 3

    # Search test
    search_res = await client.get("/api/v1/members?search=PAGE-02", headers=admin_headers)
    assert search_res.status_code == 200
    s_data = search_res.json()
    assert s_data["total"] == 1
    assert s_data["items"][0]["member_number"] == "MEM-PAGE-02"


@pytest.mark.asyncio
async def test_missing_member_returns_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    """Verify non-existent member ID returns 404 with standard envelope."""
    random_id = str(uuid.uuid4())
    res = await client.get(f"/api/v1/members/{random_id}", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"]["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_admin_exit_member_same_date_as_joined_api(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
):
    """Verify API exit on same date as join date produces 0 shares and preserves history."""
    await _open_membership(db_session, admin_user)

    same_date = "2024-04-10"
    create_res = await client.post(
        "/api/v1/members",
        json={
            "member_number": "MEM-SAME-API",
            "full_name": "Same Date API User",
            "phone": "+251911999888",
            "date_joined": same_date,
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    member_id = create_res.json()["id"]

    # Exit on same date
    exit_res = await client.post(
        f"/api/v1/members/{member_id}/exit",
        json={
            "exit_date": same_date,
            "exit_reason": "Immediate departure on same date",
        },
        headers=admin_headers,
    )
    assert exit_res.status_code == 200
    exit_data = exit_res.json()
    assert exit_data["status"] == "EXITED"
    assert exit_data["current_share_count"] == 0
    assert exit_data["current_share_value"] == "0.00"
    assert len(exit_data["shares"]) == 2
    assert exit_data["shares"][0]["share_count"] == 0
    assert exit_data["shares"][1]["share_count"] == 12

    # Query detail
    get_res = await client.get(f"/api/v1/members/{member_id}", headers=admin_headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["current_share_count"] == 0
    assert get_data["current_share_value"] == "0.00"
    assert len(get_data["shares"]) == 2
    assert get_data["shares"][0]["share_count"] == 0
    assert get_data["shares"][1]["share_count"] == 12
