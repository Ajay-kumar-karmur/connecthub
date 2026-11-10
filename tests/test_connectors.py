import pytest

from app.connectors import registry
from app.connectors.base import PermanentError, RetryableError, classify_status
from app.connectors.github_mock import GitHubMock


def test_registry_lists_connectors():
    assert registry.names() == ["github", "google"]


def test_unknown_connector_raises():
    with pytest.raises(KeyError):
        registry.get("nope")


@pytest.mark.parametrize("status", [200, 201, 204])
def test_ok_statuses_do_not_raise(status):
    classify_status(status)


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_temporary_statuses_are_retryable(status):
    with pytest.raises(RetryableError):
        classify_status(status)


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_client_errors_are_permanent(status):
    with pytest.raises(PermanentError):
        classify_status(status)


def test_github_adds_user_to_team():
    gh = GitHubMock()
    result = gh.handle("add_to_team", {"user": "asha", "team": "backend"})
    assert result["user"] == "asha"
    assert "asha" in gh.teams["backend"]


def test_github_unknown_action_is_permanent():
    with pytest.raises(PermanentError):
        GitHubMock().handle("explode", {})


def test_down_switch_makes_calls_fail_then_recover():
    gh = GitHubMock()
    gh.down = True
    with pytest.raises(RetryableError):
        gh.handle("add_to_team", {"user": "a", "team": "t"})
    assert gh.health_check() is False
    gh.down = False
    assert gh.handle("add_to_team", {"user": "a", "team": "t"})["user"] == "a"


def test_fail_next_n_fails_exactly_n_times():
    gh = GitHubMock()
    gh.fail_next_n = 2
    for _ in range(2):
        with pytest.raises(RetryableError):
            gh.handle("add_to_team", {"user": "a", "team": "t"})
    assert gh.handle("add_to_team", {"user": "a", "team": "t"})["team"] == "t"
