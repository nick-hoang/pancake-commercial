"""Conversation and message normalization plus reminder logic."""

from __future__ import annotations

from datetime import datetime

from ..models import NormalizedConversation, NormalizedMessage, StageDecision
from .noise import should_ignore_as_noise
from .roles import resolve_sender_role
from .stages import actual_stage, minutes_waiting, next_stage, parse_dt


def normalize_conversation(page_id: str, payload: dict, timezone_name: str) -> NormalizedConversation:
    sender = payload.get("from") or {}
    return NormalizedConversation(
        page_id=page_id,
        conversation_id=str(payload.get("id") or payload.get("conversation_id") or ""),
        type=str(payload.get("type") or "UNKNOWN"),
        customer_id=sender.get("id"),
        customer_name=sender.get("name"),
        tags=[str(item) for item in payload.get("tags", [])],
        assignee_ids=[str(item) for item in payload.get("assignee_ids", [])],
        seen=payload.get("seen"),
        is_replied=payload.get("is_replied"),
        inserted_at=parse_dt(payload.get("inserted_at"), timezone_name),
        updated_at=parse_dt(payload.get("updated_at"), timezone_name),
        snippet=payload.get("snippet") or payload.get("last_message", {}).get("text"),
        raw=payload,
    )


def normalize_message(page_id: str, conversation_id: str, payload: dict, timezone_name: str) -> NormalizedMessage:
    sender = payload.get("from") or {}
    return NormalizedMessage(
        page_id=page_id,
        conversation_id=conversation_id,
        message_id=payload.get("id"),
        sender_id=sender.get("id"),
        sender_name=sender.get("name"),
        text=(payload.get("message") or "").strip(),
        original_message=payload.get("original_message"),
        type=payload.get("type"),
        inserted_at=parse_dt(payload.get("inserted_at"), timezone_name),
        has_phone=payload.get("has_phone"),
        is_hidden=payload.get("is_hidden"),
        is_removed=payload.get("is_removed"),
        raw=payload,
    )


def decide_stage(
    conversation: NormalizedConversation,
    messages: list[NormalizedMessage],
    *,
    noise_patterns: list[str],
    staff_user_ids: set[str],
    last_notified_stage: int = 0,
    now: datetime | None = None,
    stage_1: int = 20,
    stage_2: int = 40,
    stage_3: int = 60,
) -> StageDecision | None:
    customer_candidate: NormalizedMessage | None = None
    for message in messages:
        if message.is_removed:
            continue
        if should_ignore_as_noise(message.text, noise_patterns):
            continue
        role = resolve_sender_role(message, conversation, staff_user_ids)
        if role == "customer":
            customer_candidate = message
            break

    if customer_candidate is None or customer_candidate.inserted_at is None:
        return None

    staff_replied = False
    for message in messages:
        if not message.inserted_at or message.inserted_at <= customer_candidate.inserted_at:
            continue
        if resolve_sender_role(message, conversation, staff_user_ids) == "staff":
            staff_replied = True
            break

    wait_minutes = minutes_waiting(customer_candidate.inserted_at, now=now)
    desired_stage = next_stage(wait_minutes, stage_1=stage_1, stage_2=stage_2, stage_3=stage_3)
    actual = actual_stage(desired_stage, last_notified_stage)
    return StageDecision(
        conversation_id=conversation.conversation_id,
        wait_minutes=wait_minutes,
        desired_stage=desired_stage,
        actual_stage=actual,
        customer_message_id=customer_candidate.message_id,
        customer_message_text=customer_candidate.text,
        staff_replied=staff_replied,
    )
