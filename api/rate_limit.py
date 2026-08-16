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
    if not bucket:
        # An empty deque left behind in _calls forever is a slow leak: every
        # distinct session/IP this process has ever seen gets one entry that
        # never goes away, even long after its window has fully expired.
        # `_record` (via the same defaultdict) transparently recreates a
        # fresh one if this key gets used again.
        del _calls[key]
    return bucket


def _allowed(key: tuple[str, str], window_seconds: float, cap: int) -> bool:
    return len(_prune(key, window_seconds)) < cap


def _record(key: tuple[str, str]) -> None:
    _calls[key].append(time.monotonic())


def _rate_limited_error(window_seconds: float) -> ApiError:
    return ApiError(
        429,
        "rate_limited",
        f"Too many requests -- try again in about {int(window_seconds // 60) or 1} minute(s).",
    )


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
        if not _allowed(session_key, window_seconds, max_calls) or not _allowed(
            ip_key, window_seconds, ip_cap
        ):
            raise _rate_limited_error(window_seconds)
        _record(session_key)
        _record(ip_key)

    return dependency


def check_ip_rate_limit(name: str, client_ip: str, max_calls: int, window_seconds: float) -> None:
    """Direct (non-dependency) IP-only check, for a call site that can't use
    the `rate_limit()` FastAPI dependency above -- namely gating new-session
    creation itself (api/sessions.py), which happens before a session (and
    so the per-session bucket key `rate_limit` needs) exists at all."""
    ip_key = (name, f"ip:{client_ip}")
    if not _allowed(ip_key, window_seconds, max_calls):
        raise _rate_limited_error(window_seconds)
    _record(ip_key)
