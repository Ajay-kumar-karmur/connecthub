import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app import circuit, models, rules
from app.config import settings
from app.connectors import registry
from app.connectors.base import PermanentError, RetryableError
from app.db import SessionLocal
from app.retry import next_delay

_stop = threading.Event()
_thread: threading.Thread | None = None


def now() -> datetime:
    return datetime.now(timezone.utc)


def expand_events(db) -> int:
    """Turn pending events into deliveries. Safe to run twice (idempotent)."""
    events = db.scalars(
        select(models.Event)
        .where(models.Event.status == "pending")
        .order_by(models.Event.id)
        .limit(10)
        .with_for_update(skip_locked=True)
    ).all()
    for ev in events:
        for step in rules.actions_for(ev.type, ev.payload):
            payload = {**rules.employee_fields(ev.payload), **step.get("args", {})}
            db.execute(
                insert(models.Delivery)
                .values(
                    event_id=ev.id,
                    app=step["app"],
                    action=step["action"],
                    payload=payload,
                    idempotency_key=f"{ev.id}:{step['app']}:{step['action']}",
                )
                .on_conflict_do_nothing(index_elements=["idempotency_key"])
            )
        ev.status = "processed"
    db.commit()
    return len(events)


def _state_for(db, app: str) -> models.AppState:
    state = db.get(models.AppState, app)
    if state is None:
        state = models.AppState(app=app, consecutive_failures=0, alerted=False)
        db.add(state)
        db.flush()
    return state


def run_deliveries(db) -> int:
    """Call the connector for each due delivery, respecting paused apps."""
    t = now()
    paused = db.scalars(
        select(models.AppState.app).where(models.AppState.paused_until > t)
    ).all()
    query = select(models.Delivery).where(
        models.Delivery.status == "pending", models.Delivery.run_at <= t
    )
    if paused:
        query = query.where(models.Delivery.app.not_in(paused))
    rows = db.scalars(
        query.order_by(models.Delivery.run_at).limit(20).with_for_update(skip_locked=True)
    ).all()

    attempted = 0
    for d in rows:
        state = _state_for(db, d.app)
        if circuit.is_paused(state):  # paused earlier in this same batch
            continue
        attempted += 1
        d.attempts += 1
        try:
            result = registry.get(d.app).handle(d.action, d.payload)
            d.status = "done"
            d.result = result
            d.last_error = None
            circuit.on_success(state, d.app)
        except RetryableError as e:
            d.last_error = str(e)
            circuit.on_failure(state, d.app, str(e))
            if d.attempts >= settings.max_attempts:
                d.status = "dead"
            else:
                d.run_at = now() + timedelta(seconds=next_delay(d.attempts))
        except (PermanentError, KeyError) as e:
            d.status = "dead"  # retrying will not help
            d.last_error = str(e)
    db.commit()
    return attempted


def run_once() -> dict:
    with SessionLocal() as db:
        expanded = expand_events(db)
    with SessionLocal() as db:
        attempted = run_deliveries(db)
    return {"events_expanded": expanded, "deliveries_attempted": attempted}


def _loop(interval: float):
    while not _stop.is_set():
        try:
            run_once()
        except Exception as e:  # keep the worker alive
            print(f"[worker] error: {e}")
        _stop.wait(interval)


def start(interval: float = 1.0):
    global _thread
    _stop.clear()
    _thread = threading.Thread(target=_loop, args=(interval,), daemon=True)
    _thread.start()


def stop():
    _stop.set()
