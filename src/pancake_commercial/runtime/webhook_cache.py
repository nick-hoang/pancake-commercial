"""Webhook runtime caches for page-scoped API access."""

from __future__ import annotations

import time

from ..client.page_api_v1 import PageApiClientV1
from ..models import PageConfig


class WebhookPageContextCache:
    def __init__(self, *, ttl_seconds: int = 300, logger=None, time_fn=None):
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.logger = logger
        self.time_fn = time_fn or time.monotonic
        self._client_cache: dict[str, PageApiClientV1] = {}
        self._staff_user_ids_cache: dict[str, tuple[float, set[str]]] = {}

    def get_client(self, page: PageConfig) -> PageApiClientV1:
        cached = self._client_cache.get(page.page_id)
        if cached is not None:
            return cached
        client = PageApiClientV1(page.page_access_token, logger=self.logger)
        self._client_cache[page.page_id] = client
        return client

    def get_staff_user_ids(self, page: PageConfig) -> set[str]:
        now = self.time_fn()
        cached = self._staff_user_ids_cache.get(page.page_id)
        if cached is not None:
            cached_at, staff_user_ids = cached
            if now - cached_at < self.ttl_seconds:
                return staff_user_ids

        client = self.get_client(page)
        users_payload = client.list_users(page.page_id)
        staff_user_ids = {
            str(item.get("id"))
            for item in users_payload.get("users", [])
            if item.get("id")
        }
        self._staff_user_ids_cache[page.page_id] = (now, staff_user_ids)
        if self.logger:
            self.logger.info("Webhook staff cache refreshed page_id=%s size=%s", page.page_id, len(staff_user_ids))
        return staff_user_ids
