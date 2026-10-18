"""
Domain exception hierarchy for the Cooperative Financial Management ERP.

Services raise these exceptions.
API routers catch them and translate to appropriate HTTP responses.

Mapping:
    NotFoundError           → 404
    BusinessValidationError → 400 / 422
    AuthorizationError      → 403
    ImmutabilityError       → 422
    InsufficientFundsError  → 422
    InvalidStateTransition  → 422
    DuplicateError          → 409
"""


class CoopException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class NotFoundError(CoopException):
    """Entity not found."""
    pass


class BusinessValidationError(CoopException):
    """Business rule validation failure."""

    def __init__(self, message: str, field_errors: dict[str, list[str]] | None = None):
        self.field_errors = field_errors or {}
        super().__init__(message, error_code="VALIDATION_ERROR")


# Alias for backwards compatibility with any early imports
ValidationError = BusinessValidationError


class AuthorizationError(CoopException):
    """Insufficient permissions for the requested operation."""
    pass


class ImmutabilityError(CoopException):
    """Attempt to mutate an immutable record (e.g., a transaction)."""
    pass


class InsufficientFundsError(CoopException):
    """Fund balance is insufficient for the requested operation."""

    def __init__(self, fund_name: str, requested: str, available: str):
        self.fund_name = fund_name
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient balance in '{fund_name}': "
            f"requested {requested}, available {available}",
            error_code="INSUFFICIENT_FUNDS",
        )


class InvalidStateTransitionError(CoopException):
    """Invalid status transition attempted."""

    def __init__(self, entity: str, current_status: str, attempted_status: str):
        super().__init__(
            f"Cannot transition {entity} from '{current_status}' to '{attempted_status}'",
            error_code="INVALID_STATE_TRANSITION",
        )


class DuplicateError(CoopException):
    """Duplicate value for a unique field."""

    def __init__(self, field: str, value: str):
        super().__init__(
            f"Duplicate value for {field}: '{value}'",
            error_code="DUPLICATE",
        )
