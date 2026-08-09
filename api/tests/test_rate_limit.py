import pytest

from api.errors import ApiError
from api.rate_limit import rate_limit


class FakeSession:
    def __init__(self, session_id):
        self.id = session_id


def test_rate_limit_allows_calls_under_the_cap():
    dependency = rate_limit("test_allows", max_calls=3, window_seconds=60)
    session = FakeSession("session-a")
    for _ in range(3):
        dependency(session)  # no raise


def test_rate_limit_blocks_once_the_cap_is_hit():
    dependency = rate_limit("test_blocks", max_calls=2, window_seconds=60)
    session = FakeSession("session-b")
    dependency(session)
    dependency(session)
    with pytest.raises(ApiError) as exc_info:
        dependency(session)
    assert exc_info.value.status_code == 429


def test_rate_limit_tracks_each_session_independently():
    dependency = rate_limit("test_per_session", max_calls=1, window_seconds=60)
    dependency(FakeSession("session-c"))
    dependency(FakeSession("session-d"))  # a different session, not blocked


def test_rate_limit_tracks_each_named_endpoint_independently():
    session = FakeSession("session-e")
    rate_limit("test_endpoint_a", max_calls=1, window_seconds=60)(session)
    rate_limit("test_endpoint_b", max_calls=1, window_seconds=60)(session)  # not blocked
