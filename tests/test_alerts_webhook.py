from __future__ import annotations

import unittest
from pathlib import Path
from uuid import uuid4

from pancake_commercial.alerts import format_stage_alert
from pancake_commercial.models import NormalizedConversation, PageConfig, StageDecision
from pancake_commercial.runtime.dedupe import SQLiteDedupeStore, compute_event_fingerprint
from pancake_commercial.runtime.webhook_server import should_trigger_reconcile


class AlertsAndWebhookTests(unittest.TestCase):
    def test_format_stage_alert_contains_core_fields(self) -> None:
        page = PageConfig(name="Main", page_id="page-1", page_access_token="x")
        conversation = NormalizedConversation(
            page_id="page-1",
            conversation_id="conv-1",
            type="INBOX",
            customer_id="cust-1",
            customer_name="Alice",
        )
        decision = StageDecision(
            conversation_id="conv-1",
            wait_minutes=42,
            desired_stage=2,
            actual_stage=1,
            customer_message_id="m-1",
            customer_message_text="Cho minh xin gia",
            staff_replied=False,
        )
        text = format_stage_alert(page, conversation, decision)
        self.assertIn("Stage 1", text)
        self.assertIn("Alice", text)
        self.assertIn("42 minutes", text)
        self.assertIn("Cho minh xin gia", text)

    def test_compute_event_fingerprint_is_stable(self) -> None:
        payload = {
            "event_type": "messaging",
            "page_id": "page-1",
            "data": {
                "conversation": {"id": "conv-1"},
                "message": {"id": "m-1"},
            },
        }
        self.assertEqual(compute_event_fingerprint(payload), compute_event_fingerprint(payload))

    def test_sqlite_dedupe_store_remembers_fingerprint(self) -> None:
        sqlite_path = Path("tests") / f".tmp-dedupe-{uuid4().hex}.sqlite"
        store = SQLiteDedupeStore(str(sqlite_path))
        fingerprint = "abc123"
        self.assertFalse(store.seen(fingerprint))
        store.remember(fingerprint, "messaging", "page-1")
        self.assertTrue(store.seen(fingerprint))

    def test_should_trigger_reconcile_for_messaging_event(self) -> None:
        self.assertTrue(should_trigger_reconcile({"event_type": "messaging", "page_id": "page-1"}))
        self.assertFalse(should_trigger_reconcile({"event_type": "post", "page_id": "page-1"}))


if __name__ == "__main__":
    unittest.main()
