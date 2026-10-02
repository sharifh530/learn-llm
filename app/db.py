"""Small SQLite transactions keep progress across application restarts."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Database:
    remote = False
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()


SCHEMA = """
                CREATE TABLE IF NOT EXISTS lesson_progress (
                    lesson_id TEXT PRIMARY KEY,
                    completed_version INTEGER,
                    completed_at TEXT,
                    last_seen_version INTEGER,
                    last_seen_at TEXT
                );
                CREATE TABLE IF NOT EXISTS acknowledgments (
                    lesson_id TEXT NOT NULL, kind TEXT NOT NULL,
                    version INTEGER NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (lesson_id, kind)
                );
                CREATE TABLE IF NOT EXISTS activity_progress (
                    activity_id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL,
                    best_score INTEGER NOT NULL DEFAULT 0,
                    passed INTEGER NOT NULL DEFAULT 0,
                    studied INTEGER NOT NULL DEFAULT 0, passed_version INTEGER,
                    question_signature TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    idempotency_key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL,
                    lesson_id TEXT NOT NULL, activity_id TEXT NOT NULL,
                    version INTEGER NOT NULL, answers TEXT NOT NULL,
                    score INTEGER NOT NULL, studied INTEGER NOT NULL,
                    response TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS xp_awards (
                    activity_id TEXT NOT NULL, kind TEXT NOT NULL,
                    amount INTEGER NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (activity_id, kind)
                );
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_id TEXT NOT NULL,
                    changed TEXT NOT NULL, learned TEXT NOT NULL,
                    confusing TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ai_requests (
                    request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL,
                    purpose TEXT NOT NULL, lesson_id TEXT,
                    status TEXT NOT NULL, created_at REAL NOT NULL,
                    provider_calls INTEGER NOT NULL DEFAULT 0,
                    input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER,
                    response TEXT, error_code TEXT
                );
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, mode TEXT NOT NULL,
                    persona TEXT NOT NULL, archived INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_turns (
                    id TEXT PRIMARY KEY, chat_id TEXT NOT NULL REFERENCES chats(id),
                    user_text TEXT NOT NULL, selected_id TEXT, created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY, turn_id TEXT NOT NULL REFERENCES chat_turns(id),
                    payload_hash TEXT NOT NULL, context_json TEXT NOT NULL,
                    status TEXT NOT NULL, text TEXT NOT NULL DEFAULT '',
                    error TEXT, error_code TEXT, finish_reason TEXT,
                    input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS chat_turn_order ON chat_turns(chat_id,created_at);
                PRAGMA user_version = 3;
            """
