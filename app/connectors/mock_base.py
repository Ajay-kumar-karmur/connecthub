import random
import time

from app.connectors.base import BaseConnector, RetryableError


class MockConnector(BaseConnector):
    """A fake app that can fail on purpose, so we can prove retries work."""

    def __init__(self):
        self.down = False
        self.failure_rate = 0.0
        self.fail_next_n = 0
        self.latency_ms = 0

    def _maybe_fail(self):
        if self.latency_ms:
            time.sleep(self.latency_ms / 1000)
        if self.down:
            raise RetryableError("503 Service Unavailable (mock is down)")
        if self.fail_next_n > 0:
            self.fail_next_n -= 1
            raise RetryableError("503 Service Unavailable (planned failure)")
        if random.random() < self.failure_rate:
            raise RetryableError("503 Service Unavailable (random failure)")

    def health_check(self) -> bool:
        return not self.down

    def status(self) -> dict:
        return {
            "name": self.name,
            "down": self.down,
            "failure_rate": self.failure_rate,
            "fail_next_n": self.fail_next_n,
            "latency_ms": self.latency_ms,
        }
