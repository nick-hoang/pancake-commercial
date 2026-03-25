"""Command-line interface for Pancake integration."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from .client.page_api_v1 import PageApiClientV1
from .client.page_api_v2 import PageApiClientV2
from .client.user_api import UserApiClient
from .config import load_config
from .errors import PancakeError
from .logging import configure_logging
from .runtime.poller import monitor_run_once


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logger = configure_logging(getattr(args, "log_level", "INFO"))
    try:
        config = load_config(getattr(args, "config", None))
        if hasattr(args, "func"):
            return args.func(args, config, logger)
        parser.print_help()
        return 1
    except PancakeError as exc:
        logger.error("%s", exc)
        return 2
    except Exception as exc:
        logger.error("%s", exc)
        return 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pancake-commercial")
    parser.add_argument("--config", help="Path to config JSON file")
    parser.add_argument("--log-level", default="INFO")
    subparsers = parser.add_subparsers(dest="command")

    health = subparsers.add_parser("healthcheck")
    health.add_argument("--page-id")
    health.set_defaults(func=cmd_healthcheck)

    pages = subparsers.add_parser("pages-list")
    pages.set_defaults(func=cmd_pages_list)

    conv = subparsers.add_parser("conversations-list")
    conv.add_argument("--page-id")
    conv.add_argument("--last-conversation-id")
    conv.set_defaults(func=cmd_conversations_list)

    msgs = subparsers.add_parser("messages-list")
    msgs.add_argument("--page-id")
    msgs.add_argument("--conversation-id", required=True)
    msgs.add_argument("--current-count", type=int)
    msgs.set_defaults(func=cmd_messages_list)

    tags = subparsers.add_parser("tags-list")
    tags.add_argument("--page-id")
    tags.set_defaults(func=cmd_tags_list)

    users = subparsers.add_parser("users-list")
    users.add_argument("--page-id")
    users.set_defaults(func=cmd_users_list)

    add_tag = subparsers.add_parser("conversation-add-tag")
    add_tag.add_argument("--page-id")
    add_tag.add_argument("--conversation-id", required=True)
    add_tag.add_argument("--tag-id", required=True)
    add_tag.add_argument("--dry-run", action="store_true")
    add_tag.set_defaults(func=cmd_conversation_add_tag)

    remove_tag = subparsers.add_parser("conversation-remove-tag")
    remove_tag.add_argument("--page-id")
    remove_tag.add_argument("--conversation-id", required=True)
    remove_tag.add_argument("--tag-id", required=True)
    remove_tag.add_argument("--dry-run", action="store_true")
    remove_tag.set_defaults(func=cmd_conversation_remove_tag)

    assign = subparsers.add_parser("conversation-assign")
    assign.add_argument("--page-id")
    assign.add_argument("--conversation-id", required=True)
    assign.add_argument("--assignee-id", action="append", required=True)
    assign.add_argument("--dry-run", action="store_true")
    assign.set_defaults(func=cmd_conversation_assign)

    read = subparsers.add_parser("conversation-mark-read")
    read.add_argument("--page-id")
    read.add_argument("--conversation-id", required=True)
    read.add_argument("--dry-run", action="store_true")
    read.set_defaults(func=cmd_conversation_mark_read)

    unread = subparsers.add_parser("conversation-mark-unread")
    unread.add_argument("--page-id")
    unread.add_argument("--conversation-id", required=True)
    unread.add_argument("--dry-run", action="store_true")
    unread.set_defaults(func=cmd_conversation_mark_unread)

    send = subparsers.add_parser("conversation-send-message")
    send.add_argument("--page-id")
    send.add_argument("--conversation-id", required=True)
    send.add_argument("--action", default="reply_inbox")
    send.add_argument("--message")
    send.add_argument("--content-id", action="append")
    send.add_argument("--sender-id")
    send.add_argument("--reply-message-id")
    send.add_argument("--message-id")
    send.add_argument("--post-id")
    send.add_argument("--from-id")
    send.add_argument("--template-id")
    send.add_argument("--dry-run", action="store_true")
    send.set_defaults(func=cmd_conversation_send_message)

    monitor = subparsers.add_parser("monitor-run-once")
    monitor.add_argument("--page-id")
    monitor.add_argument("--dry-run", action="store_true")
    monitor.set_defaults(func=cmd_monitor_run_once)

    return parser


def _get_page(config, page_id: str | None):
    if page_id:
        for page in config.pages:
            if page.page_id == page_id:
                return page
        raise ValueError(f"Page {page_id} not found in config.")
    if not config.pages:
        raise ValueError("No pages configured.")
    return config.pages[0]


def _print(data) -> int:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_healthcheck(args, config, logger) -> int:
    page = _get_page(config, getattr(args, "page_id", None))
    client = PageApiClientV1(page.page_access_token, logger=logger)
    tags = client.list_tags(page.page_id)
    return _print(
        {
            "ok": True,
            "page_id": page.page_id,
            "page_name": page.name,
            "base_url": client.base_url,
            "tags_count": len(tags.get("tags", [])),
        }
    )


def cmd_pages_list(args, config, logger) -> int:
    access_token = os.getenv("PANCAKE_USER_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("Set PANCAKE_USER_ACCESS_TOKEN to use pages-list.")
    client = UserApiClient(access_token, logger=logger)
    return _print(client.list_pages())


def cmd_conversations_list(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV2(page.page_access_token, logger=logger)
    return _print(
        client.list_conversations(
            page.page_id,
            last_conversation_id=args.last_conversation_id,
            unread_first=True,
            order_by="updated_at",
        )
    )


def cmd_messages_list(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(client.list_messages(page.page_id, args.conversation_id, current_count=args.current_count))


def cmd_tags_list(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(client.list_tags(page.page_id))


def cmd_users_list(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(client.list_users(page.page_id))


def cmd_conversation_add_tag(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(
        client.update_conversation_tag(
            page.page_id,
            args.conversation_id,
            "add",
            args.tag_id,
            dry_run=args.dry_run or config.runtime.dry_run,
        )
    )


def cmd_conversation_remove_tag(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(
        client.update_conversation_tag(
            page.page_id,
            args.conversation_id,
            "remove",
            args.tag_id,
            dry_run=args.dry_run or config.runtime.dry_run,
        )
    )


def cmd_conversation_assign(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(
        client.assign_conversation(
            page.page_id,
            args.conversation_id,
            args.assignee_id,
            dry_run=args.dry_run or config.runtime.dry_run,
        )
    )


def cmd_conversation_mark_read(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(client.mark_read(page.page_id, args.conversation_id, dry_run=args.dry_run or config.runtime.dry_run))


def cmd_conversation_mark_unread(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    return _print(client.mark_unread(page.page_id, args.conversation_id, dry_run=args.dry_run or config.runtime.dry_run))


def cmd_conversation_send_message(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    client = PageApiClientV1(page.page_access_token, logger=logger)
    payload = {"action": args.action}
    if args.message is not None:
        payload["message"] = args.message
    if args.content_id:
        payload["content_ids"] = args.content_id
    if args.sender_id:
        payload["sender_id"] = args.sender_id
    if args.reply_message_id:
        payload["reply_message_id"] = args.reply_message_id
    if args.message_id:
        payload["message_id"] = args.message_id
    if args.post_id:
        payload["post_id"] = args.post_id
    if args.from_id:
        payload["from_id"] = args.from_id
    if args.template_id:
        payload["template_id"] = args.template_id
    return _print(
        client.send_message(
            page.page_id,
            args.conversation_id,
            payload,
            dry_run=args.dry_run or config.runtime.dry_run,
        )
    )


def cmd_monitor_run_once(args, config, logger) -> int:
    page = _get_page(config, args.page_id)
    if args.dry_run:
        config.runtime.dry_run = True
    result = monitor_run_once(config, page)
    return _print(asdict(result))
