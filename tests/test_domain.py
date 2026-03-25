from __future__ import annotations

import unittest
from datetime import datetime

from pancake_commercial.domain.conversations import decide_stage
from pancake_commercial.models import NormalizedConversation, NormalizedMessage


class DomainTests(unittest.TestCase):
    def test_decide_stage_detects_customer_waiting_without_staff_reply(self) -> None:
        conversation = NormalizedConversation(
            page_id="page-1",
            conversation_id="conv-1",
            type="INBOX",
            customer_id="customer-1",
            customer_name="Customer One",
        )
        messages = [
            NormalizedMessage(
                page_id="page-1",
                conversation_id="conv-1",
                message_id="m-1",
                sender_id="customer-1",
                sender_name="Customer One",
                text="Xin tư vấn giúp mình",
                original_message=None,
                type="INBOX",
                inserted_at=datetime.fromisoformat("2026-03-25T10:00:00+07:00"),
            )
        ]

        decision = decide_stage(
            conversation,
            messages,
            noise_patterns=["ok"],
            staff_user_ids={"staff-1"},
            last_notified_stage=0,
            now=datetime.fromisoformat("2026-03-25T10:45:00+07:00"),
        )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.wait_minutes, 45)
        self.assertEqual(decision.desired_stage, 2)
        self.assertEqual(decision.actual_stage, 1)
        self.assertFalse(decision.staff_replied)

    def test_decide_stage_returns_none_for_noise(self) -> None:
        conversation = NormalizedConversation(
            page_id="page-1",
            conversation_id="conv-1",
            type="INBOX",
            customer_id="customer-1",
            customer_name="Customer One",
        )
        messages = [
            NormalizedMessage(
                page_id="page-1",
                conversation_id="conv-1",
                message_id="m-1",
                sender_id="customer-1",
                sender_name="Customer One",
                text="ok",
                original_message=None,
                type="INBOX",
                inserted_at=datetime.fromisoformat("2026-03-25T10:00:00+07:00"),
            )
        ]

        decision = decide_stage(
            conversation,
            messages,
            noise_patterns=["ok"],
            staff_user_ids=set(),
            now=datetime.fromisoformat("2026-03-25T10:45:00+07:00"),
        )

        self.assertIsNone(decision)

    def test_decide_stage_marks_staff_reply(self) -> None:
        conversation = NormalizedConversation(
            page_id="page-1",
            conversation_id="conv-1",
            type="INBOX",
            customer_id="customer-1",
            customer_name="Customer One",
        )
        messages = [
            NormalizedMessage(
                page_id="page-1",
                conversation_id="conv-1",
                message_id="m-1",
                sender_id="customer-1",
                sender_name="Customer One",
                text="Cho mình hỏi giá",
                original_message=None,
                type="INBOX",
                inserted_at=datetime.fromisoformat("2026-03-25T10:00:00+07:00"),
            ),
            NormalizedMessage(
                page_id="page-1",
                conversation_id="conv-1",
                message_id="m-2",
                sender_id="staff-1",
                sender_name="Sale One",
                text="Bên mình báo giá nhé",
                original_message=None,
                type="INBOX",
                inserted_at=datetime.fromisoformat("2026-03-25T10:05:00+07:00"),
            ),
        ]

        decision = decide_stage(
            conversation,
            messages,
            noise_patterns=["ok"],
            staff_user_ids={"staff-1"},
            now=datetime.fromisoformat("2026-03-25T10:45:00+07:00"),
        )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertTrue(decision.staff_replied)


if __name__ == "__main__":
    unittest.main()
