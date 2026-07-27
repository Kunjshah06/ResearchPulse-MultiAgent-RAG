# =============================================================================
# PaperMind AI — SQLite Database Service for User Auth & Persistence
# =============================================================================
# Zero-dependency, thread-safe SQLite database manager handling User Accounts,
# Password Hashing, Document Ownership, and Chat History Persistence.
# =============================================================================

from __future__ import annotations

import sqlite3
import hashlib
import uuid
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from papermind.core.config.settings import get_settings
from papermind.core.logging.logger import get_logger

log = get_logger(__name__)


def _hash_password(password: str, salt: str) -> str:
    """Hashes a password with SHA-256 and a per-user salt."""
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


class DatabaseService:
    """SQLite Database manager for authentication and user persistence."""

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        if db_path is None:
            settings = get_settings()
            db_dir = settings.storage.upload_dir.parent / "database"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "papermind.db"
        else:
            self.db_path = Path(db_path)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a thread-safe connection to the SQLite database."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Creates tables for users, user_documents, and chat_messages if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Users Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            # 2. User Documents Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    authors TEXT,
                    filename TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )

            # 3. Chat Messages Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.commit()
            log.info("Database initialized successfully", db_path=str(self.db_path))

    # ── User Account Operations ───────────────────────────────────────────────

    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Registers a new user with a hashed password and salt."""
        username_clean = username.strip().lower()
        email_clean = email.strip().lower()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check existing username or email
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username_clean, email_clean))
            if cursor.fetchone():
                raise ValueError("Username or Email already registered. Please sign in.")

            user_id = str(uuid.uuid4())
            salt = secrets.token_hex(16)
            password_hash = _hash_password(password, salt)
            created_at = datetime.utcnow().isoformat()

            cursor.execute(
                """
                INSERT INTO users (id, username, email, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, username_clean, email_clean, password_hash, salt, created_at),
            )
            conn.commit()

            return {
                "id": user_id,
                "username": username_clean,
                "email": email_clean,
                "created_at": created_at,
            }

    def authenticate_user(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """Verifies username/email and password credentials."""
        identifier = username_or_email.strip().lower()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (identifier, identifier),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Invalid username or password.")

            stored_hash = row["password_hash"]
            salt = row["salt"]

            if _hash_password(password, salt) != stored_hash:
                raise ValueError("Invalid username or password.")

            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "created_at": row["created_at"],
            }

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches user details by user ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    # ── User Document Persistence ─────────────────────────────────────────────

    def add_user_document(self, user_id: str, doc_id: str, filename: str, title: str, authors: str) -> Dict[str, Any]:
        """Associates an uploaded document with a specific user account."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            entry_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()

            # Prevent duplicates for same user and doc_id
            cursor.execute("SELECT id FROM user_documents WHERE user_id = ? AND doc_id = ?", (user_id, doc_id))
            if cursor.fetchone():
                return {"doc_id": doc_id, "user_id": user_id, "title": title}

            cursor.execute(
                """
                INSERT INTO user_documents (id, user_id, doc_id, filename, title, authors, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (entry_id, user_id, doc_id, filename, title, authors, created_at),
            )
            conn.commit()
            return {"id": entry_id, "user_id": user_id, "doc_id": doc_id, "title": title, "authors": authors}

    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Returns all documents uploaded by a specific user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT doc_id as id, title, authors, filename, created_at as timestamp
                FROM user_documents
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # ── Chat Messages Persistence ─────────────────────────────────────────────

    def save_chat_message(self, user_id: str, doc_id: str, role: str, content: str, citations_json: str = "[]") -> Dict[str, Any]:
        """Saves a chat message for a user and document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            msg_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()

            cursor.execute(
                """
                INSERT INTO chat_messages (id, user_id, doc_id, role, content, citations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (msg_id, user_id, doc_id, role, content, citations_json, created_at),
            )
            conn.commit()
            return {"id": msg_id, "user_id": user_id, "doc_id": doc_id, "role": role, "content": content}

    def get_chat_history(self, user_id: str, doc_id: str) -> List[Dict[str, Any]]:
        """Retrieves persistent chat history for a specific user and document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, role, content, citations_json, created_at as timestamp
                FROM chat_messages
                WHERE user_id = ? AND doc_id = ?
                ORDER BY created_at ASC
                """,
                (user_id, doc_id),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]


# Global Singleton Instance
db_service = DatabaseService()
