from collections import deque
from datetime import datetime, timezone

recent: deque = deque(maxlen=50)


def send(message: str) -> None:
    """Record and print an alert. Step 8 will also post it to Slack."""
    print(f"[ALERT] {message}")
    recent.append({"at": datetime.now(timezone.utc).isoformat(), "message": message})
