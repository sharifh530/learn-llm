from pathlib import Path
import os
from dataclasses import dataclass, field

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
    def load(cls, path=None):
        from app.settings_store import SettingsStore
        return SettingsStore(path or DATABASE_PATH.parent / "ai-settings.json").load()

    def problem(self):
        if not self.enabled:
            return "AI is disabled. Open Settings to add your Google connection."
        if self.provider != "google_cloud" or self.auth_mode not in ("express_key", "adc"):
            return "Choose google_cloud and an auth mode of express_key or adc."
        if not self.model:
            return "Choose a text model available to your Google account in Settings."
        if self.auth_mode == "express_key" and not self.api_key:
            return "Add your Google Cloud express API key in Settings."
        if self.auth_mode == "adc" and (not self.project or not self.location):
            return "Standard Cloud needs a project and location in Settings."
        return None
