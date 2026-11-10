import random


def next_delay(attempt: int, base: float = 2, cap: float = 300) -> float:
    """Seconds to wait before retry number `attempt` (1, 2, 3, ...).

    The ceiling doubles each time (2, 4, 8, 16 ...) up to `cap`.
    Picking a random value in the upper half is "jitter": it stops many
    failed calls from retrying at the same instant.
    """
    ceiling = min(cap, base**attempt)
    return random.uniform(ceiling / 2, ceiling)
