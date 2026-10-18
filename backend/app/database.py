"""
Database Engine and Session Management.

Responsibility:
    - Create async SQLAlchemy engine
    - Provide async session factory
    - Provide async session dependency for FastAPI

Dependencies:
    - sqlalchemy[asyncio]
    - asyncpg (or aiosqlite for tests)
    - app.config.settings (DATABASE_URL)

Must NOT:
    - Contain model definitions
    - Contain business logic
    - Commit transactions (services control transaction boundaries)
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

engine_kwargs: dict[str, Any] = {"echo": settings.DEBUG}
if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
        }
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session dependency for FastAPI Depends()."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
