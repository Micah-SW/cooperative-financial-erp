"""
Configuration Service.

Module: Core
See: service_contracts.md → ConfigService

Responsibility:
    - Read current and historical system configuration values
    - Update configuration with effective dating

Dependencies:
    - app.models.system_config.SystemConfig
    - app.core.audit.AuditService
"""


class ConfigService:
    """
    Manages effective-dated system configuration.

    Responsibilities:
        - Return all active config values
        - Return a specific config value (current or as-of-date)
        - Update config with effective dating (close old, create new)
        - Audit all config changes

    Must NOT:
        - Hard-code any business values
        - Delete config history
    """

    async def get_current_config(self, db):
        """Return all active config values (effective_to IS NULL). TODO (Gemini): Implement"""
        pass

    async def get_config_value(self, db, key: str, as_of_date=None):
        """Get config value, optionally as of a specific date. TODO (Gemini): Implement"""
        pass

    async def update_config(self, db, key: str, value: str, effective_from, user_id):
        """Update with effective dating. TODO (Gemini): Implement"""
        pass
