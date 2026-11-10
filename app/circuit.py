from datetime import datetime, timedelta, timezone

from app import alerts
from app.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_paused(state) -> bool:
    return bool(state.paused_until and state.paused_until > _now())


def on_failure(state, app: str, error: str) -> None:
    state.consecutive_failures += 1
    if state.consecutive_failures >= settings.failure_threshold:
        state.paused_until = _now() + timedelta(seconds=settings.pause_seconds)
        if not state.alerted:  # alert once, not once per failure
            state.alerted = True
            alerts.send(
                f"{app} paused for {settings.pause_seconds}s after "
                f"{state.consecutive_failures} failures in a row ({error})"
            )


def on_success(state, app: str) -> None:
    if state.alerted:
        alerts.send(f"{app} recovered and is working again")
        state.alerted = False
    state.consecutive_failures = 0
    state.paused_until = None
