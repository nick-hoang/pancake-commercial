"""Resolve sender roles from message and conversation data."""

from __future__ import annotations

from ..models import NormalizedConversation, NormalizedMessage


def resolve_sender_role(
    message: NormalizedMessage,
    conversation: NormalizedConversation,
    staff_user_ids: set[str],
) -> str:
    if message.sender_id and conversation.customer_id and message.sender_id == conversation.customer_id:
        return "customer"
    if message.sender_id and message.sender_id in staff_user_ids:
        return "staff"
    return "unknown"
