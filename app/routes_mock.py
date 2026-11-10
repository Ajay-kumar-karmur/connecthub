from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.connectors import registry
from app.connectors.base import PermanentError, RetryableError

router = APIRouter(prefix="/mock", tags=["mock controls"])


class TryIn(BaseModel):
    action: str
    payload: dict = {}


def _get(app_name: str):
    try:
        return registry.get(app_name)
    except KeyError:
        raise HTTPException(404, f"No connector named '{app_name}'")


@router.get("/{app_name}")
def mock_status(app_name: str):
    return _get(app_name).status()


@router.post("/{app_name}/down")
def mock_down(app_name: str):
    c = _get(app_name)
    c.down = True
    return c.status()


@router.post("/{app_name}/up")
def mock_up(app_name: str):
    c = _get(app_name)
    c.down = False
    return c.status()


@router.post("/{app_name}/fail-next/{n}")
def mock_fail_next(app_name: str, n: int):
    c = _get(app_name)
    c.fail_next_n = n
    return c.status()


@router.post("/{app_name}/try")
def mock_try(app_name: str, body: TryIn):
    """Call the connector directly, to see how it behaves."""
    c = _get(app_name)
    try:
        return c.handle(body.action, body.payload)
    except RetryableError as e:
        raise HTTPException(503, f"retryable: {e}")
    except PermanentError as e:
        raise HTTPException(400, f"permanent: {e}")
