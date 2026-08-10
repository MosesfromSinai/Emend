"""In-memory rate limiting for the endpoints that call an LLM or fetch an
arbitrary URL server-side.

Deliberately in-process, not Redis-backed: Emend runs as a single API
instance today (see infra/docker-compose.yml and the Railway deploy
workflow), so a per-process dict is enough to stop a script from running
up the Anthropic bill or using this server as an open URL-fetch proxy.
Two caveats worth knowing about, not fixing here: this resets on every
deploy/restart, and it won't coordinate across replicas if the app is ever
horizontally scaled -- both fine for the current deployment, both reasons
to move to a shared store (Redis) before either stops being true.

Two buckets, not one: sessions here are free, cookie-only, and require no
signup -- a per-session limit alone is trivially bypassed by a script that
just drops its cookie between requests, minting a brand-new session (and a
brand-new rate-limit bucket) for free every time. A second, more generous
per-IP bucket closes that gap: an attacker can churn sessions all they
want, but not the IP they're churning them from. The per-IP ceiling is
deliberately looser than the per-session one (not a tighter primary limit)
since one IP can legitimately be several real people sharing a network.
Requires uvicorn's --proxy-headers (set in infra/docker/api.Dockerfile) to
see the real client IP behind Railway's edge, rather than the edge's own
address for every request.
"""

import time
from collections import defaultdict, deque

from fastapi import Request

from api.errors import ApiError
from api.sessions import CurrentSession

_calls: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def _prune(key: tuple[str, str], window_seconds: float) -> deque[float]:
    now = time.monotonic()
    bucket = _calls[key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    return bucket


def rate_limit(name: str, max_calls: int, window_seconds: float, ip_max_calls: int | None = None):
    """FastAPI dependency factory: at most `max_calls` per session, AND at
    most `ip_max_calls` (default 3x `max_calls`) per client IP, within a
    trailing `window_seconds` window, for the endpoint identified by `name`
    (endpoints are tracked independently of each other). Checked before
    either bucket is written to, so a request rejected on one bucket never
    partially spends the other's quota."""
    ip_cap = ip_max_calls if ip_max_calls is not None else max_calls * 3

    def dependency(session: CurrentSession, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        session_key = (name, f"session:{session.id}")
        ip_key = (name, f"ip:{client_ip}")
        session_bucket = _prune(session_key, window_seconds)
        ip_bucket = _prune(ip_key, window_seconds)
        if len(session_bucket) >= max_calls or len(ip_bucket) >= ip_cap:
            raise ApiError(
                429,
                "rate_limited",
                f"Too many requests -- try again in about "
                f"{int(window_seconds // 60) or 1} minute(s).",
            )
        now = time.monotonic()
        session_bucket.append(now)
        ip_bucket.append(now)

    return dependency
