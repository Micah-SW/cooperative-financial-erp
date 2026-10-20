"""
Top-Level API Router Aggregation.

Responsibility:
    - Aggregate version 1 API routers for inclusion in FastAPI application
"""

from fastapi import APIRouter

from app.api.v1 import audit_logs, auth, config, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit"])
