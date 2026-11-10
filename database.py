"""
SQLite storage for chat sessions, messages, and application settings.
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_assistant.db")

DEFAULT_SYSTEM_PROMPT = (
    "You are KESHAV AI, an intelligent, helpful, and versatile AI assistant and website created and developed by Keshav Batra. "
    "Your creator, author, and developer is Keshav Batra. "
    "Whenever anyone asks who created, developed, made, or built you or this website/application, you must always clearly and proudly state that you and this website were created and developed by Keshav Batra. "
    "Format code snippets using markdown code blocks. Keep responses structured, informative, polite, and engaging."
)

DEFAULT_SETTINGS = {
    "provider": "gemini",  # "gemini", "openai", "demo"
    "gemini_api_key": "",
    "gemini_model": "gemini-2.0-flash-lite",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "openai_model": "gpt-4o",
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "theme_mode": "dark",
    "persona": "Helpful Assistant",
}


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                model TEXT,
                system_prompt TEXT,
                client_id TEXT DEFAULT 'default'
            )
        """)

        # Migration check: Ensure client_id column exists for multi-user isolation
        cursor.execute("PRAGMA table_info(sessions)")
        cols = [c[1] for c in cursor.fetchall()]
        if "client_id" not in cols:
            cursor.execute("ALTER TABLE sessions ADD COLUMN client_id TEXT DEFAULT 'default'")

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            )
        """)

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Prepopulate default settings if missing
        for key, value in DEFAULT_SETTINGS.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

        conn.commit()


def get_all_settings() -> Dict[str, str]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        settings = dict(DEFAULT_SETTINGS)
        for row in rows:
            settings[row["key"]] = row["value"]

        # Support GEMINI_API_KEY environment variable (e.g. from Render / Cloud hosting)
        env_gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if env_gemini_key and not settings.get("gemini_api_key", "").strip():
            settings["gemini_api_key"] = env_gemini_key

        # Ensure creator instructions are always present in the system prompt
        current_sp = settings.get("system_prompt", "")
        if "Keshav Batra" not in current_sp:
            settings["system_prompt"] = DEFAULT_SYSTEM_PROMPT
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'system_prompt'", (DEFAULT_SYSTEM_PROMPT,))
            conn.commit()
        
        # If provider was set to removed 'claude', fallback to openai or gemini
        if settings.get("provider") in ("claude", "anthropic"):
            settings["provider"] = "openai"
            cursor.execute("UPDATE settings SET value = 'openai' WHERE key = 'provider'")
            conn.commit()

        # Guard: If Gemini API key is configured, only default to 'gemini' if no other provider has been explicitly chosen
        if settings.get("gemini_api_key", "").strip() and settings.get("provider") not in ("openai", "chatgpt", "demo"):
            settings["provider"] = "gemini"

        return settings


def get_setting(key: str, default: Optional[str] = None) -> str:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row and row["value"]:
            return row["value"]

        if key == "gemini_api_key":
            env_key = os.environ.get("GEMINI_API_KEY", "").strip()
            if env_key:
                return env_key

        return default if default is not None else DEFAULT_SETTINGS.get(key, "")


def set_setting(key: str, value: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        conn.commit()


def create_session(
    title: str = "New Chat",
    system_prompt: Optional[str] = None,
    client_id: str = "default",
) -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    if system_prompt is None:
        system_prompt = get_setting("system_prompt", DEFAULT_SYSTEM_PROMPT)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (id, title, created_at, updated_at, system_prompt, client_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, title, now, now, system_prompt, client_id),
        )
        conn.commit()
    return session_id


def get_sessions(client_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if client_id is not None:
            cursor.execute(
                """
                SELECT s.id, s.title, s.created_at, s.updated_at, s.client_id,
                       (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count,
                       (SELECT content FROM messages m WHERE m.session_id = s.id ORDER BY created_at DESC LIMIT 1) AS last_message
                FROM sessions s
                WHERE s.client_id = ?
                ORDER BY s.updated_at DESC
                """,
                (client_id,),
            )
        else:
            cursor.execute(
                """
                SELECT s.id, s.title, s.created_at, s.updated_at, s.client_id,
                       (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count,
                       (SELECT content FROM messages m WHERE m.session_id = s.id ORDER BY created_at DESC LIMIT 1) AS last_message
                FROM sessions s
                ORDER BY s.updated_at DESC
                """
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def search_sessions(query: str, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches chat sessions by title AND message content, strictly scoped to client_id."""
    clean_query = query.strip()
    if not clean_query:
        return get_sessions(client_id=client_id)

    pattern = f"%{clean_query}%"
    with get_db() as conn:
        cursor = conn.cursor()
        if client_id is not None:
            cursor.execute(
                """
                SELECT DISTINCT s.id, s.title, s.created_at, s.updated_at, s.client_id,
                       (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count,
                       (SELECT content FROM messages m WHERE m.session_id = s.id ORDER BY created_at DESC LIMIT 1) AS last_message
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.id
                WHERE s.client_id = ?
                  AND (s.title LIKE ? OR m.content LIKE ?)
                ORDER BY s.updated_at DESC
                """,
                (client_id, pattern, pattern),
            )
        else:
            cursor.execute(
                """
                SELECT DISTINCT s.id, s.title, s.created_at, s.updated_at, s.client_id,
                       (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count,
                       (SELECT content FROM messages m WHERE m.session_id = s.id ORDER BY created_at DESC LIMIT 1) AS last_message
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.id
                WHERE (s.title LIKE ? OR m.content LIKE ?)
                ORDER BY s.updated_at DESC
                """,
                (pattern, pattern),
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_session_title(session_id: str, title: str):
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, session_id),
        )
        conn.commit()


def delete_session(session_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()


def add_message(session_id: str, role: str, content: str) -> Dict[str, Any]:
    msg_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (msg_id, session_id, role, content, now),
        )
        cursor.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
        conn.commit()
    return {
        "id": msg_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": now,
    }


def get_messages(session_id: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def clear_messages(session_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()


def update_message(message_id: str, new_content: str):
    """Updates content of an existing message."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET content = ? WHERE id = ?",
            (new_content, message_id),
        )
        conn.commit()


def delete_messages_after(session_id: str, message_id: str):
    """Deletes all messages in session that occurred after message_id."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        if row:
            created_at = row["created_at"]
            cursor.execute(
                "DELETE FROM messages WHERE session_id = ? AND created_at > ?",
                (session_id, created_at),
            )
            conn.commit()


def get_or_create_initial_session(client_id: Optional[str] = None) -> str:
    """Returns an empty 'New Chat' session if one already exists for this client, otherwise creates one."""
    cid = client_id or "default"
    existing = get_sessions(client_id=cid)
    for s in existing:
        if s.get("message_count", 0) == 0:
            return s["id"]
    return create_session(title="New Chat", client_id=cid)


# Automatically initialize schema on module import
init_db()
