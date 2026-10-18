"""
Pagination Utilities.

Responsibility:
    - Provide a standard paginated result wrapper
    - Provide helper to apply pagination to SQLAlchemy queries

Dependencies:
    - pydantic (BaseModel)
    - SQLAlchemy select()

Must NOT:
    - Contain business logic
    - Be domain-specific
"""

import math
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")


class PaginatedResult(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Fields:
        items: list[T]     — page of results
        total: int         — total matching records
        page: int          — current page (1-indexed)
        per_page: int      — items per page
        pages: int         — total pages
    """

    items: list[T] = Field(default_factory=list, description="Page of result items")
    total: int = Field(ge=0, description="Total matching records")
    page: int = Field(ge=1, default=1, description="Current page number (1-indexed)")
    per_page: int = Field(ge=1, default=25, description="Number of items per page")
    pages: int = Field(ge=0, default=0, description="Total number of pages")

    @model_validator(mode="before")
    @classmethod
    def compute_pages(cls, data: object) -> object:
        if isinstance(data, dict):
            total = data.get("total", 0)
            per_page = data.get("per_page", 25)
            if "pages" not in data or data.get("pages") is None:
                data["pages"] = math.ceil(total / per_page) if per_page > 0 else 0
        return data

    @classmethod
    def create(cls, items: Sequence[T], total: int, page: int, per_page: int) -> "PaginatedResult[T]":
        pages = math.ceil(total / per_page) if per_page > 0 else 0
        return cls(
            items=list(items),
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )


async def paginate(
    db: AsyncSession,
    query: Select,
    page: int = 1,
    per_page: int = 25,
) -> PaginatedResult:
    """
    Apply pagination to a SQLAlchemy select() query.

    Returns PaginatedResult with items, total count, and page metadata.
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 25

    # Count query
    count_subquery = query.order_by(None).subquery()
    count_stmt = select(func.count()).select_from(count_subquery)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one_or_none() or 0

    # Paged query
    offset = (page - 1) * per_page
    paged_stmt = query.offset(offset).limit(per_page)
    result = await db.execute(paged_stmt)
    items = result.scalars().all()

    return PaginatedResult.create(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )
