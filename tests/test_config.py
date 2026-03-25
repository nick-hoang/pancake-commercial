from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from pancake_commercial.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_resolves_env_placeholders(self) -> None:
        payload = {
            "pages": [
                {
                    "name": "example",
                    "page_id": "page-1",
                    "page_access_token": "${PANCAKE_PAGE_ACCESS_TOKEN}",
                }
            ],
            "alerts": {
                "provider": "telegram",
                "telegram_bot_token": "${TELEGRAM_BOT_TOKEN}",
                "telegram_chat_id": "${TELEGRAM_CHAT_ID}",
            },
        }

        path = Path("tests/.tmp-config.json")
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.addCleanup(path.unlink, missing_ok=True)

        os.environ["PANCAKE_PAGE_ACCESS_TOKEN"] = "page-token"
        os.environ["TELEGRAM_BOT_TOKEN"] = "bot-token"
        os.environ["TELEGRAM_CHAT_ID"] = "chat-id"
        cfg = load_config(str(path))

        self.assertEqual(cfg.pages[0].page_access_token, "page-token")
        self.assertEqual(cfg.alerts.telegram_bot_token, "bot-token")
        self.assertEqual(cfg.alerts.telegram_chat_id, "chat-id")

    def test_load_config_from_env_without_file(self) -> None:
        os.environ["PANCAKE_PAGE_ID"] = "page-2"
        os.environ["PANCAKE_PAGE_ACCESS_TOKEN"] = "page-token-2"
        os.environ["PANCAKE_PAGE_NAME"] = "prod-page"
        cfg = load_config()
        self.assertEqual(cfg.pages[0].page_id, "page-2")
        self.assertEqual(cfg.pages[0].page_access_token, "page-token-2")
        self.assertEqual(cfg.pages[0].name, "prod-page")


if __name__ == "__main__":
    unittest.main()
