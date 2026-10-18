"""
Focused Foundation Tests for Chapter 02: Repair the Foundations.

Tests verify:
- All 12 canonical enumerations including AuditAction.
- Domain exception hierarchy and BusinessValidationError.
- Generic Pydantic PaginatedResult[T] model and async paginate helper.
- Application configuration via Pydantic Settings.
- Database engine, sessionmaker, and CoopBase declarative base.
- Alembic configuration security and metadata registration.
"""

import math
import uuid
import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import Integer, String, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from app.config import Settings, settings
from app.core.enums import (
    AuditAction,
    ConfigValueType,
    ContributionStatus,
    ExpenseCategory,
    FundType,
    MemberStatus,
    ProjectStatus,
    TransactionDirection,
    TransactionType,
    UserRole,
    WithdrawalStatus,
    WithdrawalType,
)
from app.core.exceptions import (
    AuthorizationError,
    BusinessValidationError,
    CoopException,
    DuplicateError,
    ImmutabilityError,
    InsufficientFundsError,
    InvalidStateTransitionError,
    NotFoundError,
    ValidationError,
)
from app.core.pagination import PaginatedResult, paginate
from app.database import async_session_factory, engine, get_db
from app.models.base import CoopBase


class TestEnums:
    """Verify all 12 canonical enumerations and their values."""

    def test_total_canonical_enums_count(self):
        """Ensure all 12 enums are defined per the architectural blueprint."""
        enums = [
            MemberStatus,
            TransactionType,
            TransactionDirection,
            FundType,
            ContributionStatus,
            WithdrawalStatus,
            WithdrawalType,
            ExpenseCategory,
            ProjectStatus,
            UserRole,
            ConfigValueType,
            AuditAction,
        ]
        assert len(enums) == 12

    def test_audit_action_values(self):
        """Verify the 10 standard audit actions in AuditAction."""
        expected_actions = {
            "CREATE",
            "UPDATE",
            "VERIFY",
            "REVERSE",
            "APPROVE",
            "REJECT",
            "EXIT",
            "DEACTIVATE",
            "LOGIN",
            "CONFIG_CHANGE",
        }
        actual_actions = {a.value for a in AuditAction}
        assert actual_actions == expected_actions
        assert len(AuditAction) == 10

    def test_enum_string_inheritance(self):
        """Verify enums inherit from str for serialization and DB compatibility."""
        assert isinstance(AuditAction.CREATE, str)
        assert AuditAction.CREATE == "CREATE"
        assert MemberStatus.ACTIVE == "ACTIVE"
        assert TransactionDirection.CREDIT == "CREDIT"
        assert FundType.MEMBER_EQUITY == "MEMBER_EQUITY"


class TestExceptions:
    """Verify domain exception hierarchy and BusinessValidationError."""

    def test_exception_inheritance(self):
        assert issubclass(BusinessValidationError, CoopException)
        assert issubclass(NotFoundError, CoopException)
        assert issubclass(AuthorizationError, CoopException)
        assert issubclass(ImmutabilityError, CoopException)
        assert issubclass(InsufficientFundsError, CoopException)
        assert issubclass(InvalidStateTransitionError, CoopException)
        assert issubclass(DuplicateError, CoopException)

    def test_validation_error_alias_and_attributes(self):
        """Verify BusinessValidationError attributes and backward compatibility alias."""
        assert ValidationError is BusinessValidationError

        err = BusinessValidationError("Invalid contribution amount", {"amount": ["Must be > 0"]})
        assert err.message == "Invalid contribution amount"
        assert err.error_code == "VALIDATION_ERROR"
        assert err.field_errors == {"amount": ["Must be > 0"]}
        assert str(err) == "Invalid contribution amount"

    def test_insufficient_funds_error_details(self):
        err = InsufficientFundsError(fund_name="MEMBER_EQUITY", requested="5000.00", available="1200.00")
        assert err.fund_name == "MEMBER_EQUITY"
        assert err.requested == "5000.00"
        assert err.available == "1200.00"
        assert err.error_code == "INSUFFICIENT_FUNDS"
        assert "MEMBER_EQUITY" in str(err)

    def test_invalid_state_transition_error(self):
        err = InvalidStateTransitionError(entity="Member", current_status="EXITED", attempted_status="ACTIVE")
        assert err.error_code == "INVALID_STATE_TRANSITION"
        assert "Cannot transition Member from 'EXITED' to 'ACTIVE'" in str(err)

    def test_duplicate_error(self):
        err = DuplicateError(field="member_number", value="M-001")
        assert err.error_code == "DUPLICATE"
        assert "Duplicate value for member_number: 'M-001'" in str(err)


class TestPagination:
    """Verify generic PaginatedResult[T] model and automatic page calculation."""

    def test_paginated_result_instantiation(self):
        result = PaginatedResult[str](items=["item1", "item2"], total=2, page=1, per_page=10)
        assert result.items == ["item1", "item2"]
        assert result.total == 2
        assert result.page == 1
        assert result.per_page == 10
        assert result.pages == 1

    @pytest.mark.parametrize(
        "total,per_page,expected_pages",
        [
            (0, 25, 0),
            (1, 25, 1),
            (25, 25, 1),
            (26, 25, 2),
            (50, 25, 2),
            (51, 25, 3),
            (150, 25, 6),
            (10, 3, 4),
        ],
    )
    def test_automatic_pages_computation(self, total, per_page, expected_pages):
        res = PaginatedResult[int](items=[], total=total, page=1, per_page=per_page)
        assert res.pages == expected_pages

    def test_paginated_result_validation(self):
        """Negative values for total, or page < 1 must be rejected by Pydantic."""
        with pytest.raises(PydanticValidationError):
            PaginatedResult[str](items=[], total=-1, page=1, per_page=10)

        with pytest.raises(PydanticValidationError):
            PaginatedResult[str](items=[], total=10, page=0, per_page=10)

        with pytest.raises(PydanticValidationError):
            PaginatedResult[str](items=[], total=10, page=1, per_page=0)

    def test_paginated_result_create_helper(self):
        items = ["a", "b", "c"]
        res = PaginatedResult.create(items=items, total=35, page=2, per_page=10)
        assert res.items == items
        assert res.total == 35
        assert res.page == 2
        assert res.per_page == 10
        assert res.pages == 4

    @pytest.mark.asyncio
    async def test_async_paginate_helper(self):
        """Test paginate() function with an async SQLAlchemy query."""
        test_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        class TestBase(DeclarativeBase):
            pass

        class TestItem(TestBase):
            __tablename__ = "test_items"
            id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
            name: Mapped[str] = mapped_column(String(50))

        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

        # Seed 15 records
        async with session_factory() as session:
            for i in range(1, 16):
                session.add(TestItem(name=f"Item {i}"))
            await session.commit()

        # Paginate: page 2, per_page 5 -> items 6..10
        async with session_factory() as session:
            query = select(TestItem).order_by(TestItem.id)
            paged = await paginate(session, query, page=2, per_page=5)

            assert paged.total == 15
            assert paged.page == 2
            assert paged.per_page == 5
            assert paged.pages == 3
            assert len(paged.items) == 5
            assert [item.name for item in paged.items] == ["Item 6", "Item 7", "Item 8", "Item 9", "Item 10"]

        await test_engine.dispose()


class TestConfig:
    """Verify application configuration via Pydantic Settings."""

    def test_settings_defaults(self):
        cfg = Settings()
        assert cfg.DATABASE_URL.startswith("postgresql+asyncpg://")
        assert cfg.SECRET_KEY != ""
        assert cfg.JWT_ALGORITHM == "HS256"
        assert cfg.JWT_EXPIRATION_MINUTES == 480
        assert cfg.APP_NAME == "Cooperative Financial Management ERP"
        assert isinstance(cfg.DEBUG, bool)
        assert "http://localhost:3000" in cfg.CORS_ORIGINS

    def test_settings_override(self):
        custom = Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            DEBUG=True,
            APP_NAME="Custom ERP",
            CORS_ORIGINS=["https://erp.example.com"],
        )
        assert custom.DATABASE_URL == "sqlite+aiosqlite:///:memory:"
        assert custom.DEBUG is True
        assert custom.APP_NAME == "Custom ERP"
        assert custom.CORS_ORIGINS == ["https://erp.example.com"]

    def test_exported_settings_singleton(self):
        assert isinstance(settings, Settings)


class TestModelsBase:
    """Verify CoopBase declarative base configuration."""

    def test_coop_base_metadata_schema(self):
        assert CoopBase.metadata.schema == "coop"
        assert CoopBase.__abstract__ is True

    def test_coop_base_columns(self):
        assert "id" in CoopBase.__annotations__
        assert "created_at" in CoopBase.__annotations__


class TestDatabaseModule:
    """Verify database module exports and session factory."""

    def test_engine_and_session_factory_exported(self):
        assert engine is not None
        assert async_session_factory is not None

    def test_get_db_generator(self):
        gen = get_db()
        assert hasattr(gen, "__anext__")


class TestAlembicSecurity:
    """Verify Alembic configuration does not expose secrets in plaintext."""

    def test_alembic_ini_no_plain_passwords(self):
        with open("alembic.ini", "r", encoding="utf-8") as f:
            content = f.read()

        assert "coop_password" not in content
        assert "postgresql+asyncpg://coop_user:coop_password" not in content

    def test_alembic_env_registers_metadata(self):
        from pathlib import Path

        env_path = Path(__file__).parent.parent / "alembic" / "env.py"
        assert env_path.exists()
        content = env_path.read_text(encoding="utf-8")
        assert "target_metadata = CoopBase.metadata" in content
        assert "settings.DATABASE_URL" in content
        assert 'version_table_schema="coop"' in content
        assert "include_schemas=True" in content
