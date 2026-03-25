"""User-scoped Pancake APIs."""

from __future__ import annotations

from .base import BaseClient


class UserApiClient(BaseClient):
    """Client for /api/v1 user endpoints."""

    def __init__(self, access_token: str, **kwargs):
        super().__init__("https://pages.fm/api/v1", **kwargs)
        self.access_token = access_token

    def list_pages(self) -> dict:
        return self.request("GET", "/pages", params={"access_token": self.access_token})

    def generate_page_access_token(self, page_id: str) -> dict:
        return self.request(
            "POST",
            f"/pages/{page_id}/generate_page_access_token",
            params={"page_id": page_id, "access_token": self.access_token},
        )
