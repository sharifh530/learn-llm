from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
APP_DIR = ROOT / "app"
DATABASE_PATH = Path(os.environ.get("TINY_CHAT_DATABASE", str(ROOT / "data" / "tiny-chat.db")))
