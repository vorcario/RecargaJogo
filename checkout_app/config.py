"""Configuração exclusivamente do lado servidor."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    app_secret: str
    bot_api_token: str
    turbofy_api_base: str
    turbofy_client_id: str
    turbofy_client_secret: str
    turbofy_webhook_secret: str
    turbofy_webhook_url: str
    environment: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_path=Path(os.getenv("CHECKOUT_DB_PATH", "data/checkout.sqlite3")),
            app_secret=os.getenv("CHECKOUT_APP_SECRET", "development-only-change-me"),
            bot_api_token=os.getenv("BOT_API_TOKEN", ""),
            turbofy_api_base=os.getenv("TURBOFY_API_BASE", "https://api.turbofypay.com").rstrip("/"),
            turbofy_client_id=os.getenv("TURBOFY_CLIENT_ID", ""),
            turbofy_client_secret=os.getenv("TURBOFY_CLIENT_SECRET", ""),
            turbofy_webhook_secret=os.getenv("TURBOFY_WEBHOOK_SECRET", ""),
            turbofy_webhook_url=os.getenv("TURBOFY_WEBHOOK_URL", ""),
            environment=os.getenv("APP_ENV", "development"),
        )

    def assert_production_ready(self) -> None:
        if self.environment != "production":
            return
        missing = [
            name for name, value in (
                ("CHECKOUT_APP_SECRET", self.app_secret if self.app_secret != "development-only-change-me" else ""),
                ("BOT_API_TOKEN", self.bot_api_token),
                ("TURBOFY_CLIENT_ID", self.turbofy_client_id),
                ("TURBOFY_CLIENT_SECRET", self.turbofy_client_secret),
                ("TURBOFY_WEBHOOK_SECRET", self.turbofy_webhook_secret),
                ("TURBOFY_WEBHOOK_URL", self.turbofy_webhook_url),
            ) if not value
        ]
        if missing:
            raise RuntimeError(f"Configuração de produção ausente: {', '.join(missing)}")
