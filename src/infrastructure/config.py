"""
Infrastructure configuration — reads from environment variables.
This is the ONE place process.env is read in the backend.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ─────────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    secret_key: str = Field(default="change-me")
    allowed_origins: str = Field(default="http://localhost:3000")

    # ── Supabase ────────────────────────────────────────────────────────
    supabase_url: str = Field(default="")
    supabase_service_key: str = Field(default="")
    supabase_jwt_secret: str = Field(default="")

    # ── PostgreSQL ──────────────────────────────────────────────────────
    database_url: str = Field(default="postgresql+asyncpg://postgres:password@localhost:5432/overseer_ai")

    # ── Twilio ──────────────────────────────────────────────────────────
    twilio_account_sid: str = Field(default="")
    twilio_auth_token: str = Field(default="")
    twilio_phone_number: str = Field(default="")
    twilio_webhook_base_url: str = Field(default="http://localhost:8000")

    # ── ElevenLabs ──────────────────────────────────────────────────────
    elevenlabs_api_key: str = Field(default="")
    elevenlabs_voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM")
    elevenlabs_model_id: str = Field(default="eleven_turbo_v2")

    # ── WebSocket ───────────────────────────────────────────────────────
    ws_heartbeat_interval: int = Field(default=30)

    # ── Feed ingestion worker ───────────────────────────────────────────
    # Master switch for the background polling scheduler. Disabled in tests
    # and any process that should not poll (e.g. one-off CLI invocations).
    feed_ingestion_enabled: bool = Field(default=True)
    # How often the scheduler re-discovers the active feed set from the DB.
    feed_ingestion_sync_interval: int = Field(default=60)

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
