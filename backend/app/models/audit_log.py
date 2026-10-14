"""
AuditLog ORM Model.

Entity: AuditLog
Schema: coop.audit_log
Module: Core

See: database_schema.md → coop.audit_log
See: domain_model.md → AuditLog

Business Rules:
    - Audit logs are NEVER deleted or modified
    - All financial mutations MUST produce an audit log entry
    - old_values and new_values stored as JSONB

TODO (Gemini):
    - Implement using SQLAlchemy 2.0 Mapped[] style
    - Inherit from CoopBase
    - Fields: id, user_id (FK→users), action, entity_type, entity_id,
              old_values (JSONB), new_values (JSONB), ip_address, created_at
    - Indexes: (user_id), (entity_type, entity_id), (created_at)
"""

# class AuditLog(CoopBase):
#     __tablename__ = "audit_log"
#     __table_args__ = {"schema": "coop"}
#     ...
