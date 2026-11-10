from app.connectors.base import BaseConnector
from app.connectors.github_mock import GitHubMock
from app.connectors.google_mock import GoogleMock

_connectors: dict[str, BaseConnector] = {c.name: c for c in (GitHubMock(), GoogleMock())}


def get(name: str) -> BaseConnector:
    try:
        return _connectors[name]
    except KeyError:
        raise KeyError(f"No connector named '{name}'")


def names() -> list[str]:
    return sorted(_connectors)
