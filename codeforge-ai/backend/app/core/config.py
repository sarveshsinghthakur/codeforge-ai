"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    debug: bool = True
    project_name: str = "CodeForge AI"
    version: str = "1.0.0"
    api_prefix: str = "/api"

    # Database
    database_url: str = "postgresql://codeforge:codeforge@localhost:5432/codeforge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Mistral
    mistral_api_key: str = ""
    mistral_model: str = "codestral-2508"
    mistral_fallback_models: str = "mistral-small-2603,ministral-8b-2512"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Code Execution
    code_execution_timeout: int = 10
    code_execution_memory_limit: int = 256
    code_execution_cpu_limit: float = 1.0

    # Rate Limiting (requests per minute)
    rate_limit_login: int = 10
    rate_limit_register: int = 5
    rate_limit_submission: int = 30
    rate_limit_ai: int = 20
    rate_limit_generate: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
