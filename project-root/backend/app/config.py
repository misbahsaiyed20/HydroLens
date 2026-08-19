"""
Centralized app configuration, loaded from environment variables.
Keeps secrets/config out of source code (see .env.example).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/aqua_sentinel"

    # --- App ---
    app_name: str = "Aqua Sentinel API"
    environment: str = "development"
    api_prefix: str = "/api"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- Local image storage (Sprint 1 only; swap for S3/GCS later) ---
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
