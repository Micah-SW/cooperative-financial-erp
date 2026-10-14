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

TODO (Gemini):
    - Implement PaginatedResult[T] generic response model:
        items: list[T]
        total: int
        page: int
        per_page: int
        pages: int  (computed: ceil(total / per_page))
    - Implement paginate() helper that takes a SQLAlchemy query,
      applies LIMIT/OFFSET, runs COUNT, and returns PaginatedResult
"""

from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedResult(Generic[T]):
    """
    Generic paginated response wrapper.

    Fields:
        items: list[T]     — page of results
        total: int         — total matching records
        page: int          — current page (1-indexed)
        per_page: int      — items per page
        pages: int         — total pages

    TODO (Gemini): Implement as Pydantic BaseModel with Generic support
    """
    pass


async def paginate(db, query, page: int = 1, per_page: int = 25):
    """
    Apply pagination to a SQLAlchemy select() query.

    Returns PaginatedResult with items, total count, and page metadata.

    TODO (Gemini): Implement
    """
    pass
