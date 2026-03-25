from __future__ import annotations

from urllib.parse import unquote
import unittest

from pancake_commercial.logging import REDACTED, redact_mapping, redact_url


class LoggingTests(unittest.TestCase):
    def test_redact_url_hides_known_tokens(self) -> None:
        url = "https://pages.fm/api?access_token=abc&page_access_token=def&ok=1"
        redacted = unquote(redact_url(url))
        self.assertIn(f"access_token={REDACTED}", redacted)
        self.assertIn(f"page_access_token={REDACTED}", redacted)
        self.assertIn("ok=1", redacted)

    def test_redact_mapping_hides_nested_tokens(self) -> None:
        payload = {
            "page_access_token": "secret",
            "nested": {"access_token": "other-secret"},
            "items": [{"page_access_token": "x"}],
        }
        redacted = redact_mapping(payload)
        self.assertEqual(redacted["page_access_token"], REDACTED)
        self.assertEqual(redacted["nested"]["access_token"], REDACTED)
        self.assertEqual(redacted["items"][0]["page_access_token"], REDACTED)


if __name__ == "__main__":
    unittest.main()
