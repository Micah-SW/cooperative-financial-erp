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

TODO (Gemini):
    - Create Settings class extending BaseSettings
    - Fields:
        DATABASE_URL: str
        SECRET_KEY: str
        JWT_ALGORITHM: str = "HS256"
        JWT_EXPIRATION_MINUTES: int = 480
        APP_NAME: str = "Cooperative Financial Management ERP"
        DEBUG: bool = False
        CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    - Configure model_config for .env file loading
    - Export singleton: settings = Settings()
"""

# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     ...

# settings = Settings()

# TODO: Implement settings class
