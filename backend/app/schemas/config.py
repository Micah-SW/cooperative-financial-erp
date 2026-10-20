"""
System Configuration Pydantic Schemas.

Module: Core
See: api_contract.md → System Configuration
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ConfigValueType


class ConfigValue(BaseModel):
    """System configuration entry representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    config_key: str
    config_value: str
    value_type: ConfigValueType
    description: str
    effective_from: date
    effective_to: date | None = None
    created_at: datetime
    created_by: uuid.UUID


class ConfigUpdate(BaseModel):
    """Payload to update an effective-dated configuration setting."""

    config_value: str = Field(description="New configuration value in string representation")
    effective_from: date | None = Field(
        default=None,
        description="Effective start date (defaults to current date if omitted)",
    )
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Optional updated description/rationale",
    )


class ConfigHistory(BaseModel):
    """Historical timeline of configuration versions for a key."""

    config_key: str
    history: list[ConfigValue]
