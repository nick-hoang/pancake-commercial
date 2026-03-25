from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from pancake_commercial.models import AlertConfig, AppConfig, PageConfig, RuleConfig, RuntimeConfig
from pancake_commercial.runtime.poller import monitor_run_conversation_once


class PollerTests(unittest.TestCase):
    @patch("pancake_commercial.runtime.poller.create_alert_sender")
    @patch("pancake_commercial.runtime.poller.SQLiteStateStore")
    @patch("pancake_commercial.runtime.poller.PageApiClientV1")
    def test_monitor_run_conversation_once_fetches_only_target_conversation(
        self,
        mock_client_cls,
        mock_store_cls,
        mock_sender_factory,
    ) -> None:
        client = Mock()
        client.list_users.return_value = {"users": []}
        client.list_messages.return_value = {
            "messages": [
                {
                    "id": "m-1",
                    "from": {"id": "customer-1", "name": "Alice"},
                    "message": "Xin tu van giup minh",
                    "type": "INBOX",
                    "inserted_at": "2020-01-01T10:00:00+07:00",
                }
            ]
        }
        mock_client_cls.return_value = client

        store = Mock()
        store.get_last_notified_stage.return_value = 0
        mock_store_cls.return_value = store

        sender = Mock()
        mock_sender_factory.return_value = sender

        page = PageConfig(name="Main", page_id="page-1", page_access_token="token")
        config = AppConfig(
            pages=[page],
            rules=RuleConfig(noise_patterns=["ok"]),
            runtime=RuntimeConfig(dry_run=True, state_path="tests/.tmp-state.sqlite"),
            alerts=AlertConfig(provider="noop"),
        )
        raw_conversation = {
            "id": "conv-1",
            "type": "INBOX",
            "from": {"id": "customer-1", "name": "Alice"},
        }

        result = monitor_run_conversation_once(config, page, raw_conversation)

        client.list_users.assert_called_once_with("page-1")
        client.list_messages.assert_called_once_with("page-1", "conv-1")
        store.get_last_notified_stage.assert_called_once_with("page-1", "conv-1")
        sender.send_alert.assert_not_called()
        store.save_decision.assert_not_called()
        self.assertEqual(result.page_id, "page-1")
        self.assertEqual(result.processed_conversations, 1)
        self.assertEqual(result.skipped_conversations, 0)
        self.assertEqual(len(result.decisions), 1)

    @patch("pancake_commercial.runtime.poller.create_alert_sender")
    @patch("pancake_commercial.runtime.poller.SQLiteStateStore")
    @patch("pancake_commercial.runtime.poller.PageApiClientV1")
    def test_monitor_run_conversation_once_uses_cached_staff_user_ids(
        self,
        mock_client_cls,
        mock_store_cls,
        mock_sender_factory,
    ) -> None:
        client = Mock()
        client.list_messages.return_value = {
            "messages": [
                {
                    "id": "m-1",
                    "from": {"id": "customer-1", "name": "Alice"},
                    "message": "Xin tu van giup minh",
                    "type": "INBOX",
                    "inserted_at": "2020-01-01T10:00:00+07:00",
                }
            ]
        }
        mock_client_cls.return_value = client

        store = Mock()
        store.get_last_notified_stage.return_value = 0
        mock_store_cls.return_value = store

        sender = Mock()
        mock_sender_factory.return_value = sender

        page = PageConfig(name="Main", page_id="page-1", page_access_token="token")
        config = AppConfig(
            pages=[page],
            rules=RuleConfig(noise_patterns=["ok"]),
            runtime=RuntimeConfig(dry_run=True, state_path="tests/.tmp-state.sqlite"),
            alerts=AlertConfig(provider="noop"),
        )
        raw_conversation = {
            "id": "conv-1",
            "type": "INBOX",
            "from": {"id": "customer-1", "name": "Alice"},
        }

        result = monitor_run_conversation_once(
            config,
            page,
            raw_conversation,
            staff_user_ids={"staff-1"},
        )

        client.list_users.assert_not_called()
        client.list_messages.assert_called_once_with("page-1", "conv-1")
        store.get_last_notified_stage.assert_called_once_with("page-1", "conv-1")
        sender.send_alert.assert_not_called()
        store.save_decision.assert_not_called()
        self.assertEqual(result.processed_conversations, 1)
        self.assertEqual(len(result.decisions), 1)


if __name__ == "__main__":
    unittest.main()
