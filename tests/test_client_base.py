from __future__ import annotations

import unittest

from pancake_commercial.client.base import BaseClient, _normalize_query


class ClientBaseTests(unittest.TestCase):
    def test_normalize_query_formats_bool_and_list(self) -> None:
        normalized = _normalize_query(
            {
                "flag": True,
                "types": ["INBOX", "COMMENT"],
                "count": 1,
            }
        )
        self.assertEqual(normalized["flag"], "true")
        self.assertEqual(normalized["types"], ["INBOX", "COMMENT"])
        self.assertEqual(normalized["count"], 1)

    def test_dry_run_write_returns_sanitized_payload(self) -> None:
        client = BaseClient("https://pages.fm/api/public_api/v1")
        result = client.request(
            "POST",
            "/pages/page-1/conversations/conv-1/tags",
            params={"page_access_token": "secret"},
            json_body={"action": "add", "tag_id": "1"},
            dry_run=True,
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["dry_run"])
        self.assertNotIn("secret", result["url"])
        self.assertEqual(result["json_body"]["tag_id"], "1")


if __name__ == "__main__":
    unittest.main()
