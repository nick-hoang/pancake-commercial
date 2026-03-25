"""Page-scoped v2 Pancake APIs."""

from __future__ import annotations

from typing import Any

from .base import BaseClient


class PageApiClientV2(BaseClient):
    """Client for /api/public_api/v2 endpoints."""

    def __init__(self, page_access_token: str, **kwargs):
        super().__init__("https://pages.fm/api/public_api/v2", **kwargs)
        self.page_access_token = page_access_token

    def list_conversations(
        self,
        page_id: str,
        *,
        last_conversation_id: str | None = None,
        tags: str | None = None,
        conversation_type: list[str] | None = None,
        post_ids: list[str] | None = None,
        since: int | None = None,
        until: int | None = None,
        unread_first: bool | None = None,
        order_by: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {
            "page_access_token": self.page_access_token,
            "last_conversation_id": last_conversation_id,
            "tags": tags,
            "type": conversation_type,
            "post_ids": post_ids,
            "since": since,
            "until": until,
            "unread_first": unread_first,
            "order_by": order_by,
        }
        return self.request("GET", f"/pages/{page_id}/conversations", params=params)
