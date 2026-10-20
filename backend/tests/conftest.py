"""
Test Configuration and Shared Fixtures for Chapter 03.

Provides:
- In-memory SQLite async engine with attached 'coop' schema
- Isolated database session fixture
- HTTP test client with get_db dependency override
- User factories and role-based auth token fixtures
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # Register foundational models in metadata
from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models.base import CoopBase
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def test_engine():
    """Create a persistent in-memory SQLite database for the test function."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.execute(text("ATTACH DATABASE ':memory:' AS coop"))
        await conn.run_sync(CoopBase.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(CoopBase.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session for a single test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient wired to the test session."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and persist an active administrator user."""
    user = User(
        id=uuid.uuid4(),
        username="admin_test",
        email="admin_test@coop.local",
        full_name="Admin Tester",
        role=UserRole.ADMIN,
        hashed_password=hash_password("admin_pass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def treasurer_user(db_session: AsyncSession) -> User:
    """Create and persist an active treasurer user."""
    user = User(
        id=uuid.uuid4(),
        username="treasurer_test",
        email="treasurer_test@coop.local",
        full_name="Treasurer Tester",
        role=UserRole.TREASURER,
        hashed_password=hash_password("treasurer_pass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    """Create and persist an active viewer user."""
    user = User(
        id=uuid.uuid4(),
        username="viewer_test",
        email="viewer_test@coop.local",
        full_name="Viewer Tester",
        role=UserRole.VIEWER,
        hashed_password=hash_password("viewer_pass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Return JWT access token for admin_user."""
    return create_access_token(
        {"sub": str(admin_user.id), "username": admin_user.username, "role": admin_user.role}
    )


@pytest.fixture
def treasurer_token(treasurer_user: User) -> str:
    """Return JWT access token for treasurer_user."""
    return create_access_token(
        {
            "sub": str(treasurer_user.id),
            "username": treasurer_user.username,
            "role": treasurer_user.role,
        }
    )


@pytest.fixture
def viewer_token(viewer_user: User) -> str:
    """Return JWT access token for viewer_user."""
    return create_access_token(
        {"sub": str(viewer_user.id), "username": viewer_user.username, "role": viewer_user.role}
    )


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def treasurer_headers(treasurer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {treasurer_token}"}


@pytest.fixture
def viewer_headers(viewer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {viewer_token}"}
