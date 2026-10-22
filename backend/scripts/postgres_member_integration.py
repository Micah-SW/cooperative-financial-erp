"""PostgreSQL Application Integration Smoke Test.

Exercises the real FastAPI application and MemberService against the
migrated PostgreSQL database (coop_erp_live_test), validating the full
member registration, initial share allocation, duplicate rejection,
detail query, and exit lifecycle.

All database mutations occur within an explicit outer transaction that is
guaranteed to be rolled back in a finally block, leaving zero persistent artifacts.
"""

import asyncio
import os
import sys
import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# -----------------------------------------------------------------------------
# 1. Environment & Target Safety Verification (Before Engine Instantiation)
# -----------------------------------------------------------------------------

# Add backend directory to sys.path so app.* modules resolve cleanly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Read database URL exclusively from environment; do not infer or scan memory
db_url = os.environ.get("DATABASE_URL")
if not db_url or not db_url.strip():
    print(
        "FAIL: DATABASE_URL environment variable is not set. Aborting before database access.",
        file=sys.stderr,
    )
    sys.exit(1)

from sqlalchemy.engine.url import make_url

try:
    parsed_url = make_url(db_url)
except Exception:  # noqa: BLE001
    print(
        "FAIL: Malformed DATABASE_URL. Aborting before database access.",
        file=sys.stderr,
    )
    sys.exit(1)

# Enforce strict safety constraints against disposable live test database only
if parsed_url.drivername != "postgresql+asyncpg":
    print(
        f"FAIL: Safety abort - driver must be 'postgresql+asyncpg', got '{parsed_url.drivername}'.",
        file=sys.stderr,
    )
    sys.exit(1)

if parsed_url.database != "coop_erp_live_test":
    print(
        f"FAIL: Safety abort - database name must be exactly 'coop_erp_live_test', got '{parsed_url.database}'.",
        file=sys.stderr,
    )
    sys.exit(1)

if parsed_url.host not in ("localhost", "127.0.0.1"):
    print(
        f"FAIL: Safety abort - host must be localhost or 127.0.0.1, got '{parsed_url.host}'.",
        file=sys.stderr,
    )
    sys.exit(1)

if parsed_url.port != 5432:
    print(
        f"FAIL: Safety abort - port must be 5432, got '{parsed_url.port}'.",
        file=sys.stderr,
    )
    sys.exit(1)


# -----------------------------------------------------------------------------
# 2. Application & Model Imports (After Target is Strictly Validated)
# -----------------------------------------------------------------------------

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemberStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.database import engine, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.member import Member
from app.models.share import Share
from app.models.system_config import SystemConfig
from app.models.user import User

# -----------------------------------------------------------------------------
# 3. Main Integration Smoke Test Runner
# -----------------------------------------------------------------------------


async def run_integration_test() -> None:
    """Execute the end-to-end integration smoke test inside an outer transaction."""
    test_suffix = uuid.uuid4().hex[:8]
    admin_username = f"smoke_admin_{test_suffix}"
    admin_email = f"smoke_admin_{test_suffix}@example.com"
    member_number = f"MEM-{test_suffix.upper()}"

    admin_id: uuid.UUID | None = None
    member_id: uuid.UUID | None = None

    print("--- Starting PostgreSQL Application Integration Smoke Test ---")
    print(f"Target Database : {parsed_url.database}")
    print(f"Test Run ID     : {test_suffix}")

    # Preserve original dependency overrides to restore cleanly on completion
    original_overrides = dict(app.dependency_overrides)

    try:
        # Establish dedicated outer connection and transaction
        async with engine.connect() as connection:
            outer_trans = await connection.begin()
            setup_session = AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            )

            try:
                # -------------------------------------------------------------
                # Setup: Create Temporary Administrator
                # -------------------------------------------------------------
                admin_user = User(
                    id=uuid.uuid4(),
                    username=admin_username,
                    email=admin_email,
                    hashed_password=hash_password("SmokeSecret!123"),
                    full_name=f"Smoke Admin {test_suffix}",
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                setup_session.add(admin_user)
                await setup_session.flush()
                await setup_session.refresh(admin_user)
                admin_id = admin_user.id

                # Determine conflict-free configuration effective date
                stmt_max_date = select(func.max(SystemConfig.effective_from)).where(
                    SystemConfig.config_key.in_(
                        ["MEMBERSHIP_OPEN", "SHARE_VALUE", "SHARES_PER_MEMBER"]
                    )
                )
                max_existing_date = (await setup_session.execute(stmt_max_date)).scalar()
                if max_existing_date:
                    base_date = max_existing_date + timedelta(days=1)
                else:
                    base_date = date.today()

                join_date = base_date
                exit_date = base_date + timedelta(days=1)

                # Setup: Create System Configurations
                configs = [
                    SystemConfig(
                        id=uuid.uuid4(),
                        config_key="MEMBERSHIP_OPEN",
                        config_value="true",
                        value_type="BOOLEAN",
                        description="Temporary smoke test membership open flag",
                        effective_from=base_date,
                        effective_to=None,
                        created_by=admin_id,
                    ),
                    SystemConfig(
                        id=uuid.uuid4(),
                        config_key="SHARE_VALUE",
                        config_value="5000.00",
                        value_type="DECIMAL",
                        description="Temporary smoke test share value",
                        effective_from=base_date,
                        effective_to=None,
                        created_by=admin_id,
                    ),
                    SystemConfig(
                        id=uuid.uuid4(),
                        config_key="SHARES_PER_MEMBER",
                        config_value="12",
                        value_type="INTEGER",
                        description="Temporary smoke test shares per member",
                        effective_from=base_date,
                        effective_to=None,
                        created_by=admin_id,
                    ),
                ]
                for cfg in configs:
                    setup_session.add(cfg)
                await setup_session.commit()

                # Generate Admin JWT
                admin_token = create_access_token(
                    data={
                        "sub": str(admin_id),
                        "username": admin_username,
                        "role": UserRole.ADMIN.value,
                    }
                )
                auth_headers = {"Authorization": f"Bearer {admin_token}"}

                # Override get_db to share connection and create savepoints on commit
                async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
                    async with AsyncSession(
                        bind=connection,
                        join_transaction_mode="create_savepoint",
                        expire_on_commit=False,
                    ) as session:
                        yield session

                app.dependency_overrides[get_db] = override_get_db

                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://smoke-test"
                ) as client:
                    # ---------------------------------------------------------
                    # Check 1: GET /ready probe
                    # ---------------------------------------------------------
                    resp_ready = await client.get("/ready")
                    assert resp_ready.status_code == 200, (
                        f"GET /ready failed with status {resp_ready.status_code}: {resp_ready.text}"
                    )
                    ready_json = resp_ready.json()
                    assert ready_json.get("database") == "connected", (
                        f"GET /ready did not report connected database: {ready_json}"
                    )
                    print("[CHECK 1] GET /ready probe ... PASS")

                    # ---------------------------------------------------------
                    # Check 2 & 3: POST /api/v1/members (Creation & Share Allocation)
                    # ---------------------------------------------------------
                    create_payload = {
                        "member_number": member_number,
                        "full_name": f"Integration Member {test_suffix}",
                        "phone": "+251911223344",
                        "email": f"member_{test_suffix}@example.com",
                        "address": "Bole Subcity, Woreda 03, Addis Ababa",
                        "date_joined": join_date.isoformat(),
                        "notes": "PostgreSQL integration smoke test member",
                    }
                    resp_create = await client.post(
                        "/api/v1/members",
                        json=create_payload,
                        headers=auth_headers,
                    )
                    assert resp_create.status_code == 201, (
                        f"POST /api/v1/members failed with {resp_create.status_code}: {resp_create.text}"
                    )
                    created_member = resp_create.json()
                    assert created_member["member_number"] == member_number
                    assert created_member["status"] == "ACTIVE"
                    assert created_member["current_share_count"] == 12
                    assert Decimal(created_member["current_share_value"]) == Decimal(
                        "60000.00"
                    )
                    assert len(created_member["shares"]) == 1

                    init_share = created_member["shares"][0]
                    assert init_share["share_count"] == 12
                    assert Decimal(init_share["value_per_share"]) == Decimal("5000.00")
                    assert Decimal(init_share["total_value"]) == Decimal("60000.00")
                    assert init_share["effective_date"] == join_date.isoformat()

                    member_id = uuid.UUID(created_member["id"])
                    print(
                        "[CHECK 2 & 3] Admin member creation (12 shares @ 5,000 ETB, total 60,000 ETB) ... PASS"
                    )

                    # ---------------------------------------------------------
                    # Check 4: Duplicate member_number Rejection
                    # ---------------------------------------------------------
                    resp_dup = await client.post(
                        "/api/v1/members",
                        json=create_payload,
                        headers=auth_headers,
                    )
                    assert resp_dup.status_code == 409, (
                        f"Duplicate member expected 409, got {resp_dup.status_code}: {resp_dup.text}"
                    )
                    dup_json = resp_dup.json()
                    assert dup_json.get("detail", {}).get("error_code") == "DUPLICATE"

                    # Verify single member and single CREATE audit log in database
                    res_cnt = await setup_session.execute(
                        select(func.count(Member.id)).where(
                            Member.member_number == member_number
                        )
                    )
                    assert res_cnt.scalar() == 1, (
                        "Database contains multiple members for unique number"
                    )

                    res_audit_create = await setup_session.execute(
                        select(func.count(AuditLog.id)).where(
                            func.lower(AuditLog.entity_type) == "member",
                            AuditLog.entity_id == member_id,
                            AuditLog.action == "CREATE",
                        )
                    )
                    assert res_audit_create.scalar() == 1, (
                        "Expected exactly 1 CREATE audit log entry for member"
                    )
                    print(
                        "[CHECK 4] Duplicate member_number rejection (HTTP 409, single member & audit) ... PASS"
                    )

                    # ---------------------------------------------------------
                    # Check 5: Fetch Member Detail and Share History
                    # ---------------------------------------------------------
                    resp_get = await client.get(
                        f"/api/v1/members/{member_id}",
                        headers=auth_headers,
                    )
                    assert resp_get.status_code == 200, (
                        f"GET /api/v1/members/{member_id} failed: {resp_get.text}"
                    )
                    get_json = resp_get.json()
                    assert get_json["id"] == str(member_id)
                    assert get_json["member_number"] == member_number
                    assert get_json["current_share_count"] == 12
                    assert Decimal(get_json["current_share_value"]) == Decimal("60000.00")
                    assert len(get_json["shares"]) == 1
                    print(
                        "[CHECK 5] Fetch member detail and initial share history ... PASS"
                    )

                    # ---------------------------------------------------------
                    # Check 6: Process Member Exit Lifecycle
                    # ---------------------------------------------------------
                    exit_payload = {
                        "exit_date": exit_date.isoformat(),
                        "exit_reason": "Voluntary member departure for smoke test verification",
                        "notes": "Testing exit state and zero-share snapshot preservation",
                    }
                    resp_exit = await client.post(
                        f"/api/v1/members/{member_id}/exit",
                        json=exit_payload,
                        headers=auth_headers,
                    )
                    assert resp_exit.status_code == 200, (
                        f"POST /api/v1/members/{member_id}/exit failed: {resp_exit.text}"
                    )
                    exit_json = resp_exit.json()
                    assert exit_json["status"] == MemberStatus.EXITED.value
                    assert exit_json["date_exited"] == exit_date.isoformat()
                    assert exit_json["current_share_count"] == 0
                    assert Decimal(exit_json["current_share_value"]) == Decimal("0.00")
                    assert len(exit_json["shares"]) == 2

                    # History must preserve zero-share and original 12-share records
                    zero_share = exit_json["shares"][0]
                    assert zero_share["share_count"] == 0
                    assert Decimal(zero_share["total_value"]) == Decimal("0.00")
                    assert zero_share["effective_date"] == exit_date.isoformat()

                    historical_share = exit_json["shares"][1]
                    assert historical_share["share_count"] == 12
                    assert Decimal(historical_share["total_value"]) == Decimal("60000.00")
                    assert historical_share["effective_date"] == join_date.isoformat()

                    print(
                        "[CHECK 6] Member exit lifecycle and zero-share snapshot ... PASS"
                    )

                    # ---------------------------------------------------------
                    # Check 7: Audit Actions Verification
                    # ---------------------------------------------------------
                    stmt_actions = (
                        select(AuditLog.action)
                        .where(
                            func.lower(AuditLog.entity_type) == "member",
                            AuditLog.entity_id == member_id,
                        )
                        .order_by(AuditLog.created_at.asc())
                    )
                    actions = (await setup_session.execute(stmt_actions)).scalars().all()
                    assert "CREATE" in actions, "Missing CREATE action in audit log"
                    assert "EXIT" in actions, "Missing EXIT action in audit log"
                    assert len(actions) == 2, f"Expected 2 audit actions, got: {actions}"
                    print(
                        "[CHECK 7] Verification of CREATE and EXIT audit trail ... PASS"
                    )

            finally:
                # -------------------------------------------------------------
                # Cleanup: Close Session and Explicitly Roll Back Transaction
                # -------------------------------------------------------------
                try:
                    await setup_session.close()
                except Exception as close_exc:  # noqa: BLE001
                    print(
                        f"WARNING: setup_session.close() failed: {close_exc!s}",
                        file=sys.stderr,
                    )
                # Outer rollback must still run even if session close failed
                await outer_trans.rollback()

        # ---------------------------------------------------------------------
        # Check 8: Verify Complete Database Cleanup from Fresh Connection
        # ---------------------------------------------------------------------
        async with engine.connect() as verify_conn:
            # 1. Admin user must be gone
            res_u = await verify_conn.execute(
                select(func.count(User.id)).where(User.id == admin_id)
            )
            assert res_u.scalar() == 0, (
                "Cleanup assertion failed: temporary administrator was not rolled back"
            )

            # 2. Member must be gone
            if member_id:
                res_m = await verify_conn.execute(
                    select(func.count(Member.id)).where(Member.id == member_id)
                )
                assert res_m.scalar() == 0, (
                    "Cleanup assertion failed: member was not rolled back"
                )

                # 3. Shares must be gone
                res_s = await verify_conn.execute(
                    select(func.count(Share.id)).where(Share.member_id == member_id)
                )
                assert res_s.scalar() == 0, (
                    "Cleanup assertion failed: shares were not rolled back"
                )

            # 4. Audit entries must be gone
            relevant_ids = [i for i in [admin_id, member_id] if i is not None]
            res_a = await verify_conn.execute(
                select(func.count(AuditLog.id)).where(AuditLog.entity_id.in_(relevant_ids))
            )
            assert res_a.scalar() == 0, (
                "Cleanup assertion failed: audit entries were not rolled back"
            )

            # 5. Temporary configuration rows must be gone
            res_c = await verify_conn.execute(
                select(func.count(SystemConfig.id)).where(
                    SystemConfig.created_by == admin_id
                )
            )
            assert res_c.scalar() == 0, (
                "Cleanup assertion failed: temporary configs were not rolled back"
            )

        print(
            "[CHECK 8] Outer transaction rollback and clean database state verification ... PASS"
        )
        print("ALL INTEGRATION CHECKS PASSED SUCCESSFULLY.")

    finally:
        try:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(original_overrides)
        finally:
            await engine.dispose()


def main() -> None:
    """Entry point for standalone execution."""
    try:
        asyncio.run(run_integration_test())
    except Exception as exc:  # noqa: BLE001 - Standalone script entry point catches all errors for clean CLI reporting
        print(f"INTEGRATION TEST FAILED: {exc!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
