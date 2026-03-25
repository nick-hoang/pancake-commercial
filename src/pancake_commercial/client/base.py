"""Low-level HTTP client for Pancake APIs."""

from __future__ import annotations

import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..errors import (
    AuthError,
    NetworkError,
    NotFoundError,
    PancakeError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from ..logging import configure_logging, redact_mapping, redact_url


class BaseClient:
    """Shared HTTP behavior for Pancake APIs."""

    def __init__(self, base_url: str, timeout: float = 10.0, logger=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or configure_logging()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> Any:
        """Perform an HTTP request and decode JSON responses."""
        url = f"{self.base_url}{path}"
        if params:
            clean_params = {key: value for key, value in params.items() if value is not None}
            query = urlencode(_normalize_query(clean_params), doseq=True)
            url = f"{url}?{query}"

        if dry_run and method.upper() != "GET":
            return {
                "success": True,
                "dry_run": True,
                "method": method.upper(),
                "url": redact_url(url),
                "json_body": redact_mapping(json_body or {}),
            }

        body = None
        headers = {"Accept": "application/json"}
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        self.logger.debug("HTTP %s %s payload=%s", method.upper(), redact_url(url), redact_mapping(json_body or {}))
        request = Request(url=url, data=body, method=method.upper(), headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                if not payload:
                    return {"success": response.status in range(200, 300)}
                return json.loads(payload.decode("utf-8"))
        except HTTPError as exc:
            self._raise_http_error(exc)
        except (URLError, socket.timeout, TimeoutError) as exc:
            raise NetworkError(str(exc)) from exc

    def _raise_http_error(self, exc: HTTPError) -> None:
        try:
            payload = exc.read().decode("utf-8")
        except Exception:
            payload = ""

        message = f"HTTP {exc.code}: {payload or exc.reason}"
        if exc.code in (401, 403):
            raise AuthError(message) from exc
        if exc.code == 404:
            raise NotFoundError(message) from exc
        if exc.code == 409:
            raise ValidationError(message) from exc
        if exc.code == 422:
            raise ValidationError(message) from exc
        if exc.code == 429:
            raise RateLimitError(message) from exc
        if exc.code >= 500:
            raise ServerError(message) from exc
        if exc.code == 400:
            raise ValidationError(message) from exc
        if exc.code == 402:
            raise PermissionDeniedError(message) from exc
        raise PancakeError(message) from exc


def _normalize_query(params: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, bool):
            normalized[key] = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            normalized[key] = list(value)
        else:
            normalized[key] = value
    return normalized
