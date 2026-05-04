from __future__ import annotations

import threading
import time
import unittest

from pancake_commercial.runtime.webhook_queue import WebhookEventWorker


class WebhookQueueTests(unittest.TestCase):
    def test_worker_processes_enqueued_event(self) -> None:
        received = []
        worker = WebhookEventWorker(lambda payload: received.append(payload), maxsize=10)
        try:
            self.assertTrue(worker.submit({"event_type": "messaging"}))
            deadline = time.time() + 1.0
            while not received and time.time() < deadline:
                time.sleep(0.01)
            self.assertEqual(received, [{"event_type": "messaging"}])
        finally:
            worker.close()

    def test_worker_drops_when_queue_full(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def callback(payload):
            started.set()
            release.wait(timeout=0.5)

        worker = WebhookEventWorker(callback, maxsize=1)
        try:
            self.assertTrue(worker.submit({"n": 1}))
            self.assertTrue(started.wait(timeout=1.0))
            self.assertTrue(worker.submit({"n": 2}))
            self.assertFalse(worker.submit({"n": 3}))
        finally:
            release.set()
            worker.close()


if __name__ == "__main__":
    unittest.main()
