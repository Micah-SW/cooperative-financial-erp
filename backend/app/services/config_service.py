"""
System Configuration Service.

Module: Core
See: service_contracts.md → ConfigService
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_service
from app.core.enums import AuditAction, ConfigValueType
from app.core.exceptions import BusinessValidationError, NotFoundError
from app.models.system_config import SystemConfig


def validate_config_value(value: str, value_type: str | ConfigValueType) -> str:
    """Validate that the string value conforms to the expected ConfigValueType."""
    vt = value_type.value if isinstance(value_type, ConfigValueType) else str(value_type)

    if vt == ConfigValueType.DECIMAL.value:
        try:
            Decimal(value)
        except InvalidOperation:
            raise BusinessValidationError(f"Invalid decimal value: '{value}'")
    elif vt == ConfigValueType.INTEGER.value:
        try:
            int(value)
        except ValueError:
            raise BusinessValidationError(f"Invalid integer value: '{value}'")
    elif vt == ConfigValueType.BOOLEAN.value:
        if value.lower() not in ("true", "false", "1", "0"):
            raise BusinessValidationError(f"Invalid boolean value: '{value}'. Expected 'true' or 'false'")
    elif vt == ConfigValueType.STRING.value:
        if not value:
            raise BusinessValidationError("String configuration value cannot be empty")
    else:
        raise BusinessValidationError(f"Unknown configuration value type: {vt}")

    return value


class ConfigService:
    """
    Manages effective-dated system configuration.

    Preserves full historical auditability.
    """

    async def get(
        self,
        db: AsyncSession,
        key: str,
        as_of: date | None = None,
    ) -> SystemConfig:
        """
        Get active configuration record or as-of a specific date.

        Raises:
            NotFoundError: If key does not exist for the specified date.
        """
        stmt = select(SystemConfig).where(SystemConfig.config_key == key)
        if as_of is None:
            stmt = stmt.where(SystemConfig.effective_to.is_(None))
        else:
            stmt = stmt.where(
                SystemConfig.effective_from <= as_of,
                (SystemConfig.effective_to.is_(None) | (SystemConfig.effective_to >= as_of)),
            )

        stmt = stmt.order_by(SystemConfig.effective_from.desc()).limit(1)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            date_str = f" as of {as_of.isoformat()}" if as_of else ""
            raise NotFoundError(f"Configuration key '{key}' not found{date_str}")

        return record

    async def get_current_config(self, db: AsyncSession) -> list[SystemConfig]:
        """Return all active configuration values (effective_to IS NULL)."""
        stmt = (
            select(SystemConfig)
            .where(SystemConfig.effective_to.is_(None))
            .order_by(SystemConfig.config_key.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_history(self, db: AsyncSession, key: str) -> list[SystemConfig]:
        """Return chronological history for a specific configuration key."""
        stmt = (
            select(SystemConfig)
            .where(SystemConfig.config_key == key)
            .order_by(SystemConfig.effective_from.desc())
        )
        result = await db.execute(stmt)
        records = list(result.scalars().all())
        if not records:
            raise NotFoundError(f"Configuration key '{key}' not found")
        return records

    async def update_config(
        self,
        db: AsyncSession,
        key: str,
        value: str,
        effective_from: date | None,
        user_id: uuid.UUID,
        description: str | None = None,
        ip_address: str | None = None,
    ) -> SystemConfig:
        """
        Update a configuration key using effective dating.

        Closes current active record (effective_to = effective_from - 1 day)
        and inserts a new active record.
        """
        current_record = await self.get(db, key)

        eff_from = effective_from or date.today()
        if eff_from <= current_record.effective_from:
            raise BusinessValidationError(
                f"New effective date ({eff_from}) must be strictly after current effective date ({current_record.effective_from})"
            )

        # Validate value
        validate_config_value(value, current_record.value_type)

        # Close current record
        current_record.effective_to = eff_from - timedelta(days=1)

        # Create new record
        new_record = SystemConfig(
            config_key=key,
            config_value=value,
            value_type=current_record.value_type,
            description=description or current_record.description,
            effective_from=eff_from,
            effective_to=None,
            created_by=user_id,
        )
        db.add(new_record)
        await db.flush()

        await audit_service.log(
            db,
            user_id=user_id,
            action=AuditAction.CONFIG_CHANGE,
            entity_type="SystemConfig",
            entity_id=new_record.id,
            old_values={
                "config_key": key,
                "config_value": current_record.config_value,
                "effective_to": current_record.effective_to.isoformat(),
            },
            new_values={
                "config_key": key,
                "config_value": new_record.config_value,
                "effective_from": new_record.effective_from.isoformat(),
            },
            ip_address=ip_address,
        )

        return new_record


config_service = ConfigService()
