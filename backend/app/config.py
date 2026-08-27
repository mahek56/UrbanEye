"""
app/config.py – Settings loaded from .env via pydantic-settings.

All configuration lives here; nothing else imports os.environ directly.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All values can be overridden by environment variables or a `.env` file
    in the working directory.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://urbaneye:urbaneye@localhost:5432/urbaneye_db"
    )

    # ── App ────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    BACKEND_PORT: int = 8000

    # ── CORS ───────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.  "*" allows all.
    CORS_ORIGINS: str = "*"

    # ── Severity ───────────────────────────────────────────────────────────
    # Raw severity is normalised as:  min(10, raw * (10 / SEVERITY_SCALE))
    SEVERITY_SCALE: float = 8.0

    # ── Type Weights (JSON string) ─────────────────────────────────────────
    # ASSUMPTION: weights are not in the API contract.
    # Store as a JSON string so pydantic-settings can parse it from env.
    TYPE_WEIGHTS: str = (
        '{"pothole": 8.0, "road_damage": 7.0, "obstruction": 6.0, "congestion": 5.0}'
    )

    # ── Derived helpers ────────────────────────────────────────────────────
    @property
    def type_weights_dict(self) -> Dict[str, float]:
        """Return TYPE_WEIGHTS as a Python dict."""
        return json.loads(self.TYPE_WEIGHTS)

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS_ORIGINS as a list (splits on comma)."""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
