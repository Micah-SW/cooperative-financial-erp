"""
Top-Level API Router Aggregation.

Responsibility:
    - Import and include all v1 routers
    - Mount under /api/v1 prefix

TODO (Gemini):
    - Import all v1 routers
    - Create api_router = APIRouter()
    - Include each sub-router with appropriate prefix and tags:
        /auth        → auth router (tags: ["Authentication"])
        /members     → members router (tags: ["Members"])
        /contributions → contributions router (tags: ["Contributions"])
        /withdrawals → withdrawals router (tags: ["Withdrawals"])
        /funds       → funds router (tags: ["Funds"])
        /transactions → transactions router (tags: ["Transactions"])
        /projects    → projects router (tags: ["Projects"])
        /properties  → properties router (tags: ["Properties"])
        /expenses    → expenses router (tags: ["Expenses"])
        /reports     → reports router (tags: ["Reports"])
        /config      → config router (tags: ["Configuration"])
        /users       → users router (tags: ["Users"])
        /audit-logs  → audit router (tags: ["Audit"])
"""

# from fastapi import APIRouter
# api_router = APIRouter(prefix="/api/v1")
# api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# ...
