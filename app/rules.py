import json
from pathlib import Path

RULES = json.loads((Path(__file__).parent / "rules.json").read_text())


def actions_for(event_type: str, payload: dict) -> list[dict]:
    """Return every action the rules want for this event."""
    steps = []
    for rule in RULES:
        when = rule["when"]
        if when.get("event") != event_type:
            continue
        if "department" in when and when["department"] != payload.get("department"):
            continue
        steps.extend(rule["then"])
    return steps


def employee_fields(payload: dict) -> dict:
    email = payload.get("email", "")
    return {
        "user": email.split("@")[0],
        "email": email,
        "name": payload.get("name", ""),
    }
