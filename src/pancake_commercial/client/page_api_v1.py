"""Page-scoped v1 Pancake APIs."""

from __future__ import annotations

from .base import BaseClient


class PageApiClientV1(BaseClient):
    """Client for /api/public_api/v1 endpoints."""

    def __init__(self, page_access_token: str, **kwargs):
        super().__init__("https://pages.fm/api/public_api/v1", **kwargs)
        self.page_access_token = page_access_token

    def _auth(self, extra: dict | None = None) -> dict:
        params = {"page_access_token": self.page_access_token}
        if extra:
            params.update(extra)
        return params

    def list_messages(self, page_id: str, conversation_id: str, current_count: int | None = None) -> dict:
        return self.request(
            "GET",
            f"/pages/{page_id}/conversations/{conversation_id}/messages",
            params=self._auth({"current_count": current_count}),
        )

    def send_message(self, page_id: str, conversation_id: str, payload: dict, *, dry_run: bool = False) -> dict:
        return self.request(
            "POST",
            f"/pages/{page_id}/conversations/{conversation_id}/messages",
            params=self._auth(),
            json_body=payload,
            dry_run=dry_run,
        )

    def update_conversation_tag(
        self,
        page_id: str,
        conversation_id: str,
        action: str,
        tag_id: str,
        *,
        dry_run: bool = False,
    ) -> dict:
        return self.request(
            "POST",
            f"/pages/{page_id}/conversations/{conversation_id}/tags",
            params=self._auth(),
            json_body={"action": action, "tag_id": str(tag_id)},
            dry_run=dry_run,
        )

    def assign_conversation(
        self,
        page_id: str,
        conversation_id: str,
        assignee_ids: list[str],
        *,
        dry_run: bool = False,
    ) -> dict:
        return self.request(
            "POST",
            f"/pages/{page_id}/conversations/{conversation_id}/assign",
            params=self._auth(),
            json_body={"assignee_ids": assignee_ids},
            dry_run=dry_run,
        )

    def mark_read(self, page_id: str, conversation_id: str, *, dry_run: bool = False) -> dict:
        return self.request(
            "POST",
            f"/pages/{page_id}/conversations/{conversation_id}/read",
            params=self._auth(),
            dry_run=dry_run,
        )

    def mark_unread(self, page_id: str, conversation_id: str, *, dry_run: bool = False) -> dict:
        return self.request(
            "POST",
            f"/pages/{page_id}/conversations/{conversation_id}/unread",
            params=self._auth(),
            dry_run=dry_run,
        )

    def list_tags(self, page_id: str) -> dict:
        return self.request("GET", f"/pages/{page_id}/tags", params=self._auth())

    def list_users(self, page_id: str) -> dict:
        return self.request("GET", f"/pages/{page_id}/users", params=self._auth())
