"""
FastAPI Application Entry Point.

Responsibility:
    - Create and configure the FastAPI application instance
    - Register all API routers
    - Register middleware (CORS, error handling)
    - Register centralized exception handlers (domain exceptions → HTTP responses)
    - Health and readiness endpoints
    - Application lifespan management (startup/shutdown)
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessValidationError,
    DuplicateError,
    ImmutabilityError,
    InsufficientFundsError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.database import engine, get_db

# Configure application logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("coop_erp")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    logger.info("Starting up %s", settings.APP_NAME)
    yield
    logger.info("Shutting down %s — disposing database engine", settings.APP_NAME)
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Cooperative Financial Management ERP API — Backend Core",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Exception Handlers (Standard Error Envelope)
# -----------------------------------------------------------------------------


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "NOT_FOUND",
                "field_errors": {},
            }
        },
    )


@app.exception_handler(BusinessValidationError)
async def business_validation_handler(
    request: Request, exc: BusinessValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "VALIDATION_ERROR",
                "field_errors": exc.field_errors,
            }
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "UNAUTHORIZED",
                "field_errors": {},
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthorizationError)
async def authorization_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "FORBIDDEN",
                "field_errors": {},
            }
        },
    )


@app.exception_handler(ImmutabilityError)
async def immutability_handler(request: Request, exc: ImmutabilityError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "IMMUTABILITY_ERROR",
                "field_errors": {},
            }
        },
    )


@app.exception_handler(InsufficientFundsError)
async def insufficient_funds_handler(
    request: Request, exc: InsufficientFundsError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "INSUFFICIENT_FUNDS",
                "field_errors": {
                    "fund_name": [exc.fund_name],
                    "requested": [exc.requested],
                    "available": [exc.available],
                },
            }
        },
    )


@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_transition_handler(
    request: Request, exc: InvalidStateTransitionError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "INVALID_STATE_TRANSITION",
                "field_errors": {},
            }
        },
    )


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": {
                "message": exc.message,
                "error_code": "DUPLICATE",
                "field_errors": {},
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    field_errors: dict[str, list[str]] = {}
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        msg = err.get("msg", "Invalid value")
        field_errors.setdefault(loc, []).append(msg)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "message": "Request validation failed",
                "error_code": "VALIDATION_ERROR",
                "field_errors": field_errors,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": {
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "error_code": code,
                "field_errors": {},
            }
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": {
                "message": "An internal server error occurred",
                "error_code": "INTERNAL_SERVER_ERROR",
                "field_errors": {},
            }
        },
    )


# -----------------------------------------------------------------------------
# Health and Readiness Endpoints
# -----------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Liveness probe indicating application process is running."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "0.1.0",
    }


@app.get("/ready", tags=["Health"])
@app.get("/readiness", tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Readiness probe checking application dependencies (database connectivity)."""
    try:
        await db.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "database": "connected",
            },
        )
    except Exception as exc:  # noqa: BLE001 - Readiness probe must catch all connectivity errors to return 503
        logger.warning("Readiness probe check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": "Database connectivity check failed",
            },
        )


# Mount versioned API routers
app.include_router(api_router, prefix="/api/v1")
