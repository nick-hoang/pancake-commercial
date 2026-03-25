"""Webhook dedupe store."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


class SQLiteDedupeStore:
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
                CREATE TABLE IF NOT EXISTS webhook_dedupe (
                    fingerprint TEXT PRIMARY KEY,
                    event_type TEXT,
                    page_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def seen(self, fingerprint: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT fingerprint FROM webhook_dedupe WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        return row is not None

    def remember(self, fingerprint: str, event_type: str | None, page_id: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO webhook_dedupe (fingerprint, event_type, page_id) VALUES (?, ?, ?)",
                (fingerprint, event_type, page_id),
            )


def compute_event_fingerprint(payload: dict) -> str:
    event_type = payload.get("event_type")
    page_id = payload.get("page_id")
    data = payload.get("data") or {}
    message_id = (data.get("message") or {}).get("id")
    conversation_id = (data.get("conversation") or {}).get("id")
    post_id = (data.get("post") or {}).get("id")
    subscription_id = (data.get("subscription") or {}).get("id")
    seed = json.dumps(
        {
            "event_type": event_type,
            "page_id": page_id,
            "message_id": message_id,
            "conversation_id": conversation_id,
            "post_id": post_id,
            "subscription_id": subscription_id,
        },
        sort_keys=True,
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()
