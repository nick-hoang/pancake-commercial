"""Polling-based reminder workflow."""

from __future__ import annotations

from ..client.page_api_v1 import PageApiClientV1
from ..client.page_api_v2 import PageApiClientV2
from ..domain.conversations import decide_stage, normalize_conversation, normalize_message
from ..models import AppConfig, MonitorResult, PageConfig
from .state_store import SQLiteStateStore


def monitor_run_once(config: AppConfig, page: PageConfig) -> MonitorResult:
    """Run one polling pass for a page."""
    v1 = PageApiClientV1(page.page_access_token)
    v2 = PageApiClientV2(page.page_access_token)
    store = SQLiteStateStore(config.runtime.state_path)

    users_payload = v1.list_users(page.page_id)
    conversations_payload = v2.list_conversations(page.page_id, unread_first=True, order_by="updated_at")

    staff_user_ids = {
        str(item.get("id"))
        for item in users_payload.get("users", [])
        if item.get("id")
    }

    decisions = []
    skipped = 0
    for raw_conversation in conversations_payload.get("conversations", []):
        conversation = normalize_conversation(page.page_id, raw_conversation, page.timezone)
        messages_payload = v1.list_messages(page.page_id, conversation.conversation_id)
        raw_messages = list(reversed(messages_payload.get("messages", [])))
        messages = [
            normalize_message(page.page_id, conversation.conversation_id, payload, page.timezone)
            for payload in raw_messages
        ]

        last_stage = store.get_last_notified_stage(page.page_id, conversation.conversation_id)
        decision = decide_stage(
            conversation,
            messages,
            noise_patterns=config.rules.noise_patterns,
            staff_user_ids=staff_user_ids,
            last_notified_stage=last_stage,
            stage_1=config.rules.stage_1_minutes,
            stage_2=config.rules.stage_2_minutes,
            stage_3=config.rules.stage_3_minutes,
        )
        if decision is None or decision.staff_replied or decision.actual_stage == 0:
            skipped += 1
            continue

        decisions.append(decision)
        if not config.runtime.dry_run:
            target_message = next((item for item in messages if item.message_id == decision.customer_message_id), None)
            store.save_decision(
                page.page_id,
                conversation.conversation_id,
                customer_message_id=decision.customer_message_id,
                customer_message_at=target_message.inserted_at.isoformat() if target_message and target_message.inserted_at else None,
                actual_stage=decision.actual_stage,
            )

    return MonitorResult(
        page_id=page.page_id,
        processed_conversations=len(conversations_payload.get("conversations", [])),
        decisions=decisions,
        skipped_conversations=skipped,
    )
