"""SQLite-backed monitor state store."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteStateStore:
    """Persist last-notified state for conversations."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_state (
                    page_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    last_customer_message_id TEXT,
                    last_customer_message_at TEXT,
                    last_notified_stage INTEGER NOT NULL DEFAULT 0,
                    last_alert_at TEXT,
                    handoff_done INTEGER NOT NULL DEFAULT 0,
                    last_processed_at TEXT,
                    PRIMARY KEY (page_id, conversation_id)
                )
                """
            )

    def get_last_notified_stage(self, page_id: str, conversation_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_notified_stage FROM conversation_state WHERE page_id = ? AND conversation_id = ?",
                (page_id, conversation_id),
            ).fetchone()
        return int(row[0]) if row else 0

    def save_decision(
        self,
        page_id: str,
        conversation_id: str,
        *,
        customer_message_id: str | None,
        customer_message_at: str | None,
        actual_stage: int,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_state (
                    page_id,
                    conversation_id,
                    last_customer_message_id,
                    last_customer_message_at,
                    last_notified_stage,
                    last_processed_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(page_id, conversation_id)
                DO UPDATE SET
                    last_customer_message_id = excluded.last_customer_message_id,
                    last_customer_message_at = excluded.last_customer_message_at,
                    last_notified_stage = excluded.last_notified_stage,
                    last_processed_at = CURRENT_TIMESTAMP
                """,
                (page_id, conversation_id, customer_message_id, customer_message_at, actual_stage),
            )
