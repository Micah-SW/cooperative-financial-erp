"""
Configuration API Router.

Endpoints:
    GET    /              — All current config values (ALL roles)
    GET    /{key}         — Specific active config value (ALL roles)
    GET    /{key}/history — Historical versions of a config key (ADMIN only)
    PUT    /{key}         — Update config value with effective dating (ADMIN only)

See: api_contract.md → System Configuration
"""


from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.core.enums import UserRole
from app.models.user import User
from app.schemas.config import ConfigHistory, ConfigUpdate, ConfigValue
from app.services.config_service import config_service

router = APIRouter()


@router.get("", response_model=list[ConfigValue])
async def list_current_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConfigValue]:
    """Retrieve all currently active system configuration values."""
    records = await config_service.get_current_config(db)
    return [ConfigValue.model_validate(r) for r in records]


@router.get("/{key}/history", response_model=ConfigHistory)
async def get_config_history(
    key: str,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ConfigHistory:
    """Retrieve full chronological history for a configuration key (ADMIN only)."""
    records = await config_service.get_history(db, key)
    return ConfigHistory(
        config_key=key,
        history=[ConfigValue.model_validate(r) for r in records],
    )


@router.get("/{key}", response_model=ConfigValue)
async def get_config_key(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConfigValue:
    """Retrieve the active configuration value for a key."""
    record = await config_service.get(db, key)
    return ConfigValue.model_validate(record)


@router.put("/{key}", response_model=ConfigValue)
async def update_config_key(
    key: str,
    payload: ConfigUpdate,
    request: Request,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ConfigValue:
    """Update configuration value using effective dating (ADMIN only)."""
    client_ip = request.client.host if request.client else None
    new_record = await config_service.update_config(
        db,
        key=key,
        value=payload.config_value,
        effective_from=payload.effective_from,
        user_id=admin_user.id,
        description=payload.description,
        ip_address=client_ip,
    )
    await db.commit()
    return ConfigValue.model_validate(new_record)
