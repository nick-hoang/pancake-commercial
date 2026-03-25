"""Core data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class PageConfig:
    name: str
    page_id: str
    page_access_token: str
    enabled: bool = True
    timezone: str = "Asia/Bangkok"


@dataclass(slots=True)
class StaffMapping:
    key: str
    name: str
    tag_id: str
    alert_target: str | None = None
    user_id: str | None = None
    escalation_targets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RuleConfig:
    stage_1_minutes: int = 20
    stage_2_minutes: int = 40
    stage_3_minutes: int = 60
    noise_patterns: list[str] = field(default_factory=lambda: ["xin chao", "da", "ok", "vang"])


@dataclass(slots=True)
class RuntimeConfig:
    dry_run: bool = True
    poll_interval_seconds: int = 300
    state_backend: str = "sqlite"
    state_path: str = ".pancake_monitor_state.sqlite"
    log_level: str = "INFO"


@dataclass(slots=True)
class AlertConfig:
    provider: str = "noop"
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


@dataclass(slots=True)
class AppConfig:
    pages: list[PageConfig]
    staff_mapping: dict[str, StaffMapping] = field(default_factory=dict)
    rules: RuleConfig = field(default_factory=RuleConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)


@dataclass(slots=True)
class NormalizedConversation:
    page_id: str
    conversation_id: str
    type: str
    customer_id: str | None
    customer_name: str | None
    tags: list[str] = field(default_factory=list)
    assignee_ids: list[str] = field(default_factory=list)
    seen: bool | None = None
    is_replied: bool | None = None
    inserted_at: datetime | None = None
    updated_at: datetime | None = None
    snippet: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedMessage:
    page_id: str
    conversation_id: str
    message_id: str | None
    sender_id: str | None
    sender_name: str | None
    text: str
    original_message: str | None
    type: str | None
    inserted_at: datetime | None
    has_phone: bool | None = None
    is_hidden: bool | None = None
    is_removed: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StageDecision:
    conversation_id: str
    wait_minutes: int
    desired_stage: int
    actual_stage: int
    customer_message_id: str | None
    customer_message_text: str
    staff_replied: bool


@dataclass(slots=True)
class MonitorResult:
    page_id: str
    processed_conversations: int
    decisions: list[StageDecision] = field(default_factory=list)
    skipped_conversations: int = 0
