"""Stage progression and time helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


UTC_TZ = timezone.utc


def parse_dt(value: str | None, timezone_name: str = "Asia/Bangkok") -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    else:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC_TZ)
    return parsed.astimezone(ZoneInfo(timezone_name))


def minutes_waiting(since: datetime, now: datetime | None = None) -> int:
    reference = now or datetime.now(tz=since.tzinfo or UTC_TZ)
    delta = reference - since
    return max(0, int(delta.total_seconds() // 60))


def next_stage(wait_minutes: int, stage_1: int = 20, stage_2: int = 40, stage_3: int = 60) -> int:
    if wait_minutes >= stage_3:
        return 3
    if wait_minutes >= stage_2:
        return 2
    if wait_minutes >= stage_1:
        return 1
    return 0


def actual_stage(desired_stage: int, last_notified_stage: int) -> int:
    return min(desired_stage, last_notified_stage + 1)
