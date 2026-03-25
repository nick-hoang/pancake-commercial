"""Noise filtering helpers."""

from __future__ import annotations


def should_ignore_as_noise(text: str | None, noise_patterns: list[str]) -> bool:
    if not text:
        return True
    normalized = text.strip().lower()
    return normalized in {pattern.strip().lower() for pattern in noise_patterns}
