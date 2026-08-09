"""In-memory per-session rate limiting for the endpoints that call an LLM
or fetch an arbitrary URL server-side.

Deliberately in-process, not Redis-backed: Emend runs as a single API
instance today (see infra/docker-compose.yml and the Railway deploy
workflow), so a per-process dict is enough to stop a script from running
up the Anthropic bill or using this server as an open URL-fetch proxy.
Sessions here are free, cookie-only, and require no signup, which is
exactly what makes an unbounded LLM-backed endpoint cheap to abuse -- this
closes that gap without adding a new infrastructure dependency for a
single-instance deployment. Two caveats worth knowing about, not fixing
here: this resets on every deploy/restart, and it won't coordinate across
replicas if the app is ever horizontally scaled -- both fine for the
current deployment, both reasons to move to a shared store (Redis) before
either stops being true.
"""

import time
from collections import defaultdict, deque

from api.errors import ApiError
from api.sessions import CurrentSession

_calls: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def rate_limit(name: str, max_calls: int, window_seconds: float):
    """FastAPI dependency factory: at most `max_calls` per session within
    a trailing `window_seconds` window, for the endpoint identified by
    `name` (endpoints are tracked independently of each other)."""

    def dependency(session: CurrentSession) -> None:
        now = time.monotonic()
        bucket = _calls[(name, str(session.id))]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= max_calls:
            raise ApiError(
                429,
                "rate_limited",
                f"Too many requests -- try again in about "
                f"{int(window_seconds // 60) or 1} minute(s).",
            )
        bucket.append(now)

    return dependency
