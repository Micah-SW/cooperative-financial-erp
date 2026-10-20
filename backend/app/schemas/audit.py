"""
Audit Log Pydantic Schemas.

Module: Core
See: domain_model.md → AuditLog
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Audit log entry representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    entity_type: str
    entity_id: uuid.UUID
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime
