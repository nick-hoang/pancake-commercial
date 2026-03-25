"""Configuration loading."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .models import AlertConfig, AppConfig, PageConfig, RuleConfig, RuntimeConfig, StaffMapping


ENV_PATTERN = re.compile(r"^\$\{([A-Z0-9_]+)\}$")


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(path: str | None = None) -> AppConfig:
    """Load configuration from JSON file or environment."""
    if path:
        data = _load_json(Path(path))
        return _parse_config(data)
    return _load_from_env()


def _resolve_secret(value: str | None, env_key: str | None = None) -> str | None:
    if value is None:
        return os.getenv(env_key) if env_key else None
    if not isinstance(value, str):
        return value
    match = ENV_PATTERN.match(value.strip())
    if match:
        return os.getenv(match.group(1))
    if env_key and value.strip() == "":
        return os.getenv(env_key)
    return value


def _parse_config(data: dict) -> AppConfig:
    pages = [
        PageConfig(
            name=page.get("name") or page["page_id"],
            page_id=page["page_id"],
            page_access_token=_resolve_secret(page.get("page_access_token"), "PANCAKE_PAGE_ACCESS_TOKEN") or "",
            enabled=page.get("enabled", True),
            timezone=page.get("timezone", "Asia/Bangkok"),
        )
        for page in data.get("pages", [])
    ]

    staff_mapping = {
        key: StaffMapping(
            key=key,
            name=value.get("name", key),
            tag_id=str(value["tag_id"]),
            alert_target=value.get("alert_target") or value.get("telegram"),
            user_id=value.get("user_id"),
            escalation_targets=list(value.get("escalation_targets", [])),
        )
        for key, value in data.get("staff_mapping", data.get("staff", {})).items()
    }

    rules_data = data.get("rules", {})
    runtime_data = data.get("runtime", {})
    alert_data = data.get("alerts", {})

    return AppConfig(
        pages=pages,
        staff_mapping=staff_mapping,
        rules=RuleConfig(
            stage_1_minutes=int(rules_data.get("stage_1_minutes", 20)),
            stage_2_minutes=int(rules_data.get("stage_2_minutes", 40)),
            stage_3_minutes=int(rules_data.get("stage_3_minutes", 60)),
            noise_patterns=list(rules_data.get("noise_patterns", ["xin chao", "da", "ok", "vang"])),
        ),
        runtime=RuntimeConfig(
            dry_run=bool(runtime_data.get("dry_run", True)),
            poll_interval_seconds=int(runtime_data.get("poll_interval_seconds", 300)),
            state_backend=runtime_data.get("state_backend", "sqlite"),
            state_path=runtime_data.get("state_path", ".pancake_monitor_state.sqlite"),
            log_level=runtime_data.get("log_level", "INFO"),
        ),
        alerts=AlertConfig(
            provider=alert_data.get("provider", "noop"),
            telegram_bot_token=_resolve_secret(alert_data.get("telegram_bot_token"), "TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_resolve_secret(alert_data.get("telegram_chat_id"), "TELEGRAM_CHAT_ID"),
        ),
    )


def _load_from_env() -> AppConfig:
    page_id = os.getenv("PANCAKE_PAGE_ID")
    page_access_token = os.getenv("PANCAKE_PAGE_ACCESS_TOKEN")
    if not page_id or not page_access_token:
        raise ValueError("Provide --config or set PANCAKE_PAGE_ID and PANCAKE_PAGE_ACCESS_TOKEN.")

    page = PageConfig(
        name=os.getenv("PANCAKE_PAGE_NAME", page_id),
        page_id=page_id,
        page_access_token=page_access_token,
        timezone=os.getenv("PANCAKE_TIMEZONE", "Asia/Bangkok"),
    )
    return AppConfig(
        pages=[page],
        runtime=RuntimeConfig(
            dry_run=os.getenv("PANCAKE_DRY_RUN", "true").lower() != "false",
            state_path=os.getenv("PANCAKE_STATE_PATH", ".pancake_monitor_state.sqlite"),
            log_level=os.getenv("PANCAKE_LOG_LEVEL", "INFO"),
        ),
    )
