"""Error types for Pancake integration."""

from __future__ import annotations


class PancakeError(Exception):
    """Base Pancake integration error."""


class AuthError(PancakeError):
    """Authentication or authorization failed."""


class PermissionDeniedError(PancakeError):
    """The caller lacks permission for this operation."""


class ValidationError(PancakeError):
    """The request was invalid."""


class NotFoundError(PancakeError):
    """The requested resource was not found."""


class RateLimitError(PancakeError):
    """The caller was rate limited."""


class ServerError(PancakeError):
    """The remote server returned a 5xx response."""


class NetworkError(PancakeError):
    """The request failed due to timeout or network issues."""
