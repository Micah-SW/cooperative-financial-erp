"""
Application Configuration via Environment Variables.

Responsibility:
    - Load all configuration from environment variables / .env file
    - Provide typed, validated settings to the application
    - Single source for all environment-driven configuration

Dependencies:
    - pydantic-settings (BaseSettings)

Must NOT:
    - Contain business logic
    - Contain business-rule configuration (those go in system_config table)
    - Hard-code sensitive values
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://coop_user:coop_password@localhost:5432/coop_erp",
        description="Async database connection string",
    )
    SECRET_KEY: str = Field(
        default="change-me-to-a-real-secret-key",
        description="Secret key for JWT generation/validation",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_EXPIRATION_MINUTES: int = Field(
        default=480, description="Access token expiration in minutes"
    )
    APP_NAME: str = Field(
        default="Cooperative Financial Management ERP",
        description="Application name",
    )
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )


settings = Settings()
