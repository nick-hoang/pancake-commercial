from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from pancake_commercial.models import PageConfig
from pancake_commercial.runtime.webhook_cache import WebhookPageContextCache


class WebhookCacheTests(unittest.TestCase):
    @patch("pancake_commercial.runtime.webhook_cache.PageApiClientV1")
    def test_reuses_client_per_page(self, mock_client_cls) -> None:
        client = Mock()
        mock_client_cls.return_value = client
        cache = WebhookPageContextCache(ttl_seconds=300)
        page = PageConfig(name="Main", page_id="page-1", page_access_token="token")

        first = cache.get_client(page)
        second = cache.get_client(page)

        self.assertIs(first, second)
        mock_client_cls.assert_called_once_with("token", logger=None)

    @patch("pancake_commercial.runtime.webhook_cache.PageApiClientV1")
    def test_reuses_staff_ids_within_ttl(self, mock_client_cls) -> None:
        client = Mock()
        client.list_users.return_value = {"users": [{"id": "staff-1"}]}
        mock_client_cls.return_value = client
        ticks = iter([0.0, 10.0])
        cache = WebhookPageContextCache(ttl_seconds=60, time_fn=lambda: next(ticks))
        page = PageConfig(name="Main", page_id="page-1", page_access_token="token")

        first = cache.get_staff_user_ids(page)
        second = cache.get_staff_user_ids(page)

        self.assertEqual(first, {"staff-1"})
        self.assertEqual(second, {"staff-1"})
        client.list_users.assert_called_once_with("page-1")

    @patch("pancake_commercial.runtime.webhook_cache.PageApiClientV1")
    def test_refreshes_staff_ids_after_ttl(self, mock_client_cls) -> None:
        client = Mock()
        client.list_users.side_effect = [
            {"users": [{"id": "staff-1"}]},
            {"users": [{"id": "staff-2"}]},
        ]
        mock_client_cls.return_value = client
        ticks = iter([0.0, 120.0])
        cache = WebhookPageContextCache(ttl_seconds=60, time_fn=lambda: next(ticks))
        page = PageConfig(name="Main", page_id="page-1", page_access_token="token")

        first = cache.get_staff_user_ids(page)
        second = cache.get_staff_user_ids(page)

        self.assertEqual(first, {"staff-1"})
        self.assertEqual(second, {"staff-2"})
        self.assertEqual(client.list_users.call_count, 2)


if __name__ == "__main__":
    unittest.main()
