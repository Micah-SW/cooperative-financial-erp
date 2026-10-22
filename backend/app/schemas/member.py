"""
Member Pydantic Schemas.

Module: Member
See: api_contract.md → Members
See: service_contracts.md → MemberService
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.core.enums import MemberStatus

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class MemberCreate(BaseModel):
    """Payload to register a new cooperative member."""

    member_number: str = Field(
        min_length=1,
        max_length=20,
        description="Unique member identifier code",
    )
    full_name: str = Field(
        min_length=1,
        max_length=100,
        description="Member full legal name",
    )
    phone: str = Field(
        min_length=5,
        max_length=20,
        description="Contact phone number",
    )
    email: str | None = Field(
        default=None,
        pattern=EMAIL_REGEX,
        max_length=255,
        description="Optional contact email address",
    )
    address: str | None = Field(
        default=None,
        description="Residential / postal address",
    )
    date_joined: date = Field(
        description="Date membership was established",
    )
    notes: str | None = Field(
        default=None,
        description="Administrative notes",
    )

    @model_validator(mode="before")
    @classmethod
    def clean_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ("member_number", "full_name", "phone"):
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
        return data


class MemberUpdate(BaseModel):
    """
    Payload for updating mutable member fields.

    Prohibits updating member_number and status.
    """

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated full legal name",
    )
    phone: str | None = Field(
        default=None,
        min_length=5,
        max_length=20,
        description="Updated phone number",
    )
    email: str | None = Field(
        default=None,
        pattern=EMAIL_REGEX,
        max_length=255,
        description="Updated email address",
    )
    address: str | None = Field(
        default=None,
        description="Updated address",
    )
    notes: str | None = Field(
        default=None,
        description="Updated administrative notes",
    )

    @model_validator(mode="before")
    @classmethod
    def reject_immutable_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "member_number" in data:
                raise ValueError("Field 'member_number' is immutable and cannot be updated")
            if "status" in data:
                raise ValueError(
                    "Member status cannot be updated directly; use designated lifecycle endpoints"
                )
            for field in ("full_name", "phone"):
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
        return data


class MemberExitRequest(BaseModel):
    """Payload to record an authorized member exit lifecycle event."""

    exit_date: date = Field(description="Official membership termination date")
    exit_reason: str = Field(min_length=1, description="Documented justification for exit")
    notes: str | None = Field(default=None, description="Additional administrative remarks")


# Backward compatibility alias for any legacy imports
MemberExit = MemberExitRequest


class ShareResponse(BaseModel):
    """Representation of an immutable share allocation / valuation snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_id: uuid.UUID
    share_count: int
    value_per_share: Decimal
    total_value: Decimal
    effective_date: date
    created_at: datetime

    @field_serializer("value_per_share", "total_value", when_used="json")
    def serialize_decimal(self, v: Decimal) -> str:
        return f"{v:.2f}"


class MemberSummary(BaseModel):
    """Concise representation of a member for lists and directories."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_number: str
    full_name: str
    phone: str
    status: MemberStatus
    date_joined: date
    current_share_count: int
    current_share_value: Decimal

    @field_serializer("current_share_value", when_used="json")
    def serialize_share_value(self, v: Decimal) -> str:
        return f"{v:.2f}"

    @model_validator(mode="after")
    def enforce_exited_share_state(self) -> "MemberSummary":
        if self.status == MemberStatus.EXITED:
            self.current_share_count = 0
            self.current_share_value = Decimal("0.00")
        return self


class MemberDetail(BaseModel):
    """Comprehensive member profile including share history snapshots."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_number: str
    full_name: str
    phone: str
    status: MemberStatus
    date_joined: date
    current_share_count: int
    current_share_value: Decimal
    email: str | None = None
    address: str | None = None
    date_exited: date | None = None
    exit_reason: str | None = None
    notes: str | None = None
    shares: list[ShareResponse] = Field(default_factory=list)

    @field_serializer("current_share_value", when_used="json")
    def serialize_share_value(self, v: Decimal) -> str:
        return f"{v:.2f}"

    @field_validator("shares", mode="after")
    @classmethod
    def ensure_deterministic_shares_order(
        cls, v: list[ShareResponse]
    ) -> list[ShareResponse]:
        """Ensure share history is deterministically ordered by effective_date DESC, created_at DESC."""
        def _key(s: ShareResponse):
            created = s.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            else:
                created = created.astimezone(UTC)
            is_extinguishing = 1 if s.share_count == 0 else 0
            return (s.effective_date, created, is_extinguishing)

        return sorted(v, key=_key, reverse=True)

    @model_validator(mode="after")
    def enforce_exited_share_state(self) -> "MemberDetail":
        if self.status == MemberStatus.EXITED:
            self.current_share_count = 0
            self.current_share_value = Decimal("0.00")
        return self
