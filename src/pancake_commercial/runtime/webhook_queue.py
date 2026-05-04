"""Webhook event queue and worker."""

from __future__ import annotations

import queue
import threading


class WebhookEventWorker:
    def __init__(self, event_callback, *, logger=None, maxsize: int = 1000):
        self.event_callback = event_callback
        self.logger = logger
        self._queue: queue.Queue[dict | None] = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def submit(self, payload: dict) -> bool:
        try:
            self._queue.put_nowait(payload)
            return True
        except queue.Full:
            if self.logger:
                self.logger.error("Webhook queue full; dropping event")
            return False

    def close(self, timeout: float = 5.0) -> None:
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while True:
            payload = self._queue.get()
            if payload is None:
                return
            try:
                self.event_callback(payload)
            except Exception as exc:
                if self.logger:
                    self.logger.error("Webhook callback error: %s", exc)
            finally:
                self._queue.task_done()
