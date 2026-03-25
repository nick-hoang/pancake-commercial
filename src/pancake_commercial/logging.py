"""Logging helpers with token redaction."""

from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REDACTED = "***REDACTED***"
TOKEN_KEYS = {"page_access_token", "access_token"}


def redact_url(url: str) -> str:
    """Redact known auth tokens from a URL."""
    parts = urlsplit(url)
    query_items = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key in TOKEN_KEYS and value:
            query_items.append((key, REDACTED))
        else:
            query_items.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query_items), parts.fragment))


def redact_mapping(value: object) -> object:
    """Redact auth keys inside a dict-like object for logging."""
    if isinstance(value, dict):
        return {
            key: (REDACTED if key in TOKEN_KEYS and item else redact_mapping(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    return value


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the package logger."""
    logger = logging.getLogger("pancake_commercial")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    return logger
