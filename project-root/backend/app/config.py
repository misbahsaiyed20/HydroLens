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

    # --- Gemini vision analysis (Sprint 2) ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_api_base: str = "https://generativelanguage.googleapis.com/v1beta"

    # --- Evidence fusion (Sprint 3) ---
    related_report_radius_meters: float = 300.0
    related_report_time_window_minutes: int = 120
    baseline_minimum_observations: int = 5
    corroboration_saturation_count: int = 4
    confidence_high_threshold: float = 0.70
    confidence_moderate_threshold: float = 0.40

    # --- Actionability (Sprint 4) ---
    # Minimum corroborating (supporting) reports for HIGH confidence + HIGH
    # severity to still escalate to PRIORITY_REVIEW rather than REVIEW_RECOMMENDED.
    priority_review_min_supporting_count: int = 3

    # --- Authentication ---
    # No default in production: an empty/placeholder secret would let anyone
    # forge tokens. Tests set this via env (see conftest.py); real deployments
    # must set JWT_SECRET_KEY in their environment (see .env.example).
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24h

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
