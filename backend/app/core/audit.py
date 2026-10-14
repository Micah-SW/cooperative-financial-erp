"""
Audit Logging Service.

Responsibility:
    - Record all sensitive actions as append-only audit log entries
    - Capture before/after state for mutations
    - Participate in the caller's database transaction (no independent commit)

Dependencies:
    - app.models.audit_log.AuditLog
    - SQLAlchemy AsyncSession (injected by caller)

Must NOT:
    - Commit transactions (caller controls the boundary)
    - Be skipped for any financial mutation
    - Delete or update audit log entries
    - Filter or redact audit data

Audit Contract:
    Every service that mutates financial data MUST call:
        audit_service.log(db, user_id=..., action=..., entity_type=..., entity_id=..., ...)

    Actions: CREATE, UPDATE, VERIFY, REVERSE, APPROVE, REJECT, EXIT, DEACTIVATE, LOGIN, CONFIG_CHANGE

TODO (Gemini):
    - Implement AuditService class
    - Implement log() method per the service_contracts.md specification
    - Implement list_logs() for admin viewing
"""


class AuditService:
    """
    Append-only audit event recorder.

    Responsibilities:
        - Record audit events within the caller's transaction
        - Capture old_values / new_values as JSONB
        - Support querying by entity, user, date range

    Must NOT:
        - Commit the transaction
        - Update or delete existing audit records
    """

    async def log(
        self,
        db,  # AsyncSession
        *,
        user_id,      # UUID — who performed the action
        action,       # str — CREATE, UPDATE, VERIFY, REVERSE, etc.
        entity_type,  # str — Member, Contribution, Transaction, etc.
        entity_id,    # UUID — which record
        old_values=None,  # dict | None — state before (for updates)
        new_values=None,  # dict | None — state after
        ip_address=None,  # str | None — request origin
    ):
        """
        Create an audit log entry within the current transaction.
        TODO (Gemini): Implement
        """
        pass

    async def list_logs(self, db, *, filters, page, per_page):
        """
        Paginated audit log query. ADMIN only.
        TODO (Gemini): Implement
        """
        pass
