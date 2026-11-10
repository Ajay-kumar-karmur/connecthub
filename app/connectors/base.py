from abc import ABC, abstractmethod


class RetryableError(Exception):
    """Temporary problem (timeout, 429, 5xx). Trying again later may work."""


class PermanentError(Exception):
    """Retrying will not help (bad config, 4xx, unknown action)."""


def classify_status(status: int) -> None:
    """Raise the right error for an HTTP status code. Return nothing if OK."""
    if status < 400:
        return
    if status == 429 or status >= 500:
        raise RetryableError(f"HTTP {status}")
    raise PermanentError(f"HTTP {status}")


class BaseConnector(ABC):
    name: str = ""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the external app is reachable."""

    @abstractmethod
    def handle(self, action: str, payload: dict) -> dict:
        """Perform one action in the external app and return a result."""
