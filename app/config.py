from pathlib import Path
import os
from dataclasses import dataclass, field
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
APP_DIR = ROOT / "app"
DATABASE_PATH = Path(os.environ.get("TINY_CHAT_DATABASE", str(ROOT / "data" / "tiny-chat.db")))


@dataclass(frozen=True)
class AISettings:
    enabled: bool = False
    provider: str = "google_cloud"
    auth_mode: str = "express_key"
    api_key: str = field(default="", repr=False)
    project: str = ""
    location: str = ""
    model: str = ""

    @classmethod
    def load(cls):
        # OS variables take precedence. The ignored .env stays on this server.
        values = {**dotenv_values(ROOT / ".env"), **os.environ}
        def value(name, default=""):
            return (values.get(name) or default).strip()
        return cls(value("AI_ENABLED", "false").lower() == "true",
                   value("AI_PROVIDER", "google_cloud"), value("GOOGLE_AUTH_MODE", "express_key"),
                   value("GOOGLE_CLOUD_API_KEY"), value("GOOGLE_CLOUD_PROJECT"),
                   value("GOOGLE_CLOUD_LOCATION"), value("GOOGLE_MODEL"))

    def problem(self):
        if not self.enabled:
            return "AI is disabled. Configure the server .env, then restart the app."
        if self.provider != "google_cloud" or self.auth_mode not in ("express_key", "adc"):
            return "Choose google_cloud and an auth mode of express_key or adc."
        if not self.model:
            return "Set GOOGLE_MODEL to a text model available to your Google project."
        if self.auth_mode == "express_key" and not self.api_key:
            return "Set GOOGLE_CLOUD_API_KEY to your Cloud express key on the server."
        if self.auth_mode == "adc" and (not self.project or not self.location):
            return "ADC needs GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION."
        return None
