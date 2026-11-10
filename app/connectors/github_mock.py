from app.connectors.base import PermanentError
from app.connectors.mock_base import MockConnector


class GitHubMock(MockConnector):
    name = "github"

    def __init__(self):
        super().__init__()
        self.teams: dict[str, set[str]] = {}

    def handle(self, action: str, payload: dict) -> dict:
        self._maybe_fail()
        if action in ("add_to_team", "remove_from_team"):
            if "user" not in payload or "team" not in payload:
                raise PermanentError("payload needs 'user' and 'team'")
            members = self.teams.setdefault(payload["team"], set())
            if action == "add_to_team":
                members.add(payload["user"])
            else:
                members.discard(payload["user"])
            return {"action": action, "user": payload["user"], "team": payload["team"]}
        raise PermanentError(f"unknown action: {action}")
