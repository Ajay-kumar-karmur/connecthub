from app.connectors.base import PermanentError
from app.connectors.mock_base import MockConnector


class GoogleMock(MockConnector):
    name = "google"

    def __init__(self):
        super().__init__()
        self.accounts: dict[str, str] = {}

    def handle(self, action: str, payload: dict) -> dict:
        self._maybe_fail()
        if action in ("create_account", "disable_account"):
            if "email" not in payload:
                raise PermanentError("payload needs 'email'")
            self.accounts[payload["email"]] = (
                "active" if action == "create_account" else "disabled"
            )
            return {"action": action, "email": payload["email"]}
        raise PermanentError(f"unknown action: {action}")
