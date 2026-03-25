"""Minimal Pancake webhook receiver."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .dedupe import SQLiteDedupeStore, compute_event_fingerprint


def should_trigger_reconcile(payload: dict) -> bool:
    return payload.get("event_type") == "messaging" and bool(payload.get("page_id"))


def serve_webhook(host: str, port: int, path: str, state_path: str, logger=None, event_callback=None) -> None:
    store = SQLiteDedupeStore(state_path)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != path:
                self.send_response(404)
                self.end_headers()
                return

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
                fingerprint = compute_event_fingerprint(payload)
                duplicate = store.seen(fingerprint)
                if not duplicate:
                    store.remember(fingerprint, payload.get("event_type"), payload.get("page_id"))
                if logger:
                    logger.info(
                        "Webhook received path=%s event_type=%s duplicate=%s",
                        self.path,
                        payload.get("event_type"),
                        duplicate,
                    )
                body = json.dumps({"ok": True, "duplicate": duplicate}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                if not duplicate and event_callback and should_trigger_reconcile(payload):
                    threading.Thread(target=event_callback, args=(payload,), daemon=True).start()
            except Exception as exc:
                if logger:
                    logger.error("Webhook error: %s", exc)
                body = json.dumps({"ok": False}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer((host, port), Handler)
    if logger:
        logger.info("Webhook server listening on http://%s:%s%s", host, port, path)
    try:
        server.serve_forever()
    finally:
        server.server_close()
