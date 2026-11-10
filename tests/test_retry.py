from types import SimpleNamespace

from app import alerts, circuit
from app.retry import next_delay


def fresh_state():
    return SimpleNamespace(consecutive_failures=0, paused_until=None, alerted=False)


def test_first_retry_delay_is_short():
    for _ in range(50):
        assert 1 <= next_delay(1) <= 2


def test_delay_never_exceeds_cap():
    for attempt in range(1, 30):
        assert 0 < next_delay(attempt, cap=300) <= 300


def test_circuit_stays_closed_below_threshold():
    s = fresh_state()
    for _ in range(circuit.settings.failure_threshold - 1):
        circuit.on_failure(s, "github", "503")
    assert s.paused_until is None
    assert not circuit.is_paused(s)


def test_circuit_opens_and_alerts_once():
    alerts.recent.clear()
    s = fresh_state()
    for _ in range(circuit.settings.failure_threshold + 3):
        circuit.on_failure(s, "github", "503")
    assert circuit.is_paused(s)
    assert len(alerts.recent) == 1


def test_success_closes_circuit_and_alerts_recovery():
    alerts.recent.clear()
    s = fresh_state()
    for _ in range(circuit.settings.failure_threshold):
        circuit.on_failure(s, "github", "503")
    circuit.on_success(s, "github")
    assert not circuit.is_paused(s)
    assert s.consecutive_failures == 0
    assert len(alerts.recent) == 2  # one "paused", one "recovered"


def test_is_paused_false_for_new_state():
    assert circuit.is_paused(fresh_state()) is False
