"""
FastAPI Application Entry Point.

Responsibility:
    - Create and configure the FastAPI application instance
    - Register all API routers
    - Register middleware (CORS, error handling)
    - Register exception handlers (domain exceptions → HTTP responses)
    - Lifespan events (startup/shutdown)

Dependencies:
    - app.config.Settings
    - app.api.router (aggregated router)
    - app.core.exceptions (exception handlers)
    - app.database (engine lifecycle)

Must NOT:
    - Contain business logic
    - Import service classes directly
    - Define route handlers here

TODO (Gemini):
    - Create FastAPI app with metadata (title, version, description)
    - Add CORSMiddleware with configurable origins
    - Register the v1 router under /api/v1
    - Register exception handlers mapping domain exceptions to HTTP responses:
        NotFoundError → 404
        ValidationError → 400/422
        AuthorizationError → 403
        ImmutabilityError → 422
        InsufficientFundsError → 422
        InvalidStateTransitionError → 422
        DuplicateError → 409
    - Add lifespan for database engine startup/shutdown
"""

# from fastapi import FastAPI
# from app.config import settings
# from app.api.router import api_router

# app = FastAPI(...)

# TODO: Implement application setup
