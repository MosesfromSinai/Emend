import pytest

from api.errors import ApiError
from api.rate_limit import check_ip_rate_limit, rate_limit


class FakeSession:
    def __init__(self, session_id):
        self.id = session_id


class FakeClient:
    def __init__(self, host):
        self.host = host


class FakeRequest:
    def __init__(self, ip="203.0.113.1"):
        self.client = FakeClient(ip)


def test_rate_limit_allows_calls_under_the_cap():
    dependency = rate_limit("test_allows", max_calls=3, window_seconds=60)
    session = FakeSession("session-a")
    for _ in range(3):
        dependency(session, FakeRequest())  # no raise


def test_rate_limit_blocks_once_the_cap_is_hit():
    dependency = rate_limit("test_blocks", max_calls=2, window_seconds=60)
    session = FakeSession("session-b")
    request = FakeRequest()
    dependency(session, request)
    dependency(session, request)
    with pytest.raises(ApiError) as exc_info:
        dependency(session, request)
    assert exc_info.value.status_code == 429


def test_rate_limit_tracks_each_session_independently():
    dependency = rate_limit("test_per_session", max_calls=1, window_seconds=60)
    dependency(FakeSession("session-c"), FakeRequest("203.0.113.2"))
    dependency(FakeSession("session-d"), FakeRequest("203.0.113.3"))  # different session+IP


def test_rate_limit_tracks_each_named_endpoint_independently():
    session = FakeSession("session-e")
    request = FakeRequest()
    rate_limit("test_endpoint_a", max_calls=1, window_seconds=60)(session, request)
    rate_limit("test_endpoint_b", max_calls=1, window_seconds=60)(session, request)  # not blocked


def test_rate_limit_blocks_session_churn_from_the_same_ip():
    # the exact bypass this bucket exists for: a script drops its cookie
    # between requests to mint a fresh session (and a fresh session-level
    # allowance) for free every time -- the IP-level cap still catches it
    dependency = rate_limit("test_ip_cap", max_calls=1, window_seconds=60, ip_max_calls=3)
    same_ip = FakeRequest("203.0.113.9")
    dependency(FakeSession("session-f1"), same_ip)
    dependency(FakeSession("session-f2"), same_ip)
    dependency(FakeSession("session-f3"), same_ip)
    with pytest.raises(ApiError) as exc_info:
        dependency(FakeSession("session-f4"), same_ip)
    assert exc_info.value.status_code == 429


def test_rate_limit_ip_cap_does_not_affect_a_different_ip():
    dependency = rate_limit("test_ip_isolation", max_calls=1, window_seconds=60, ip_max_calls=1)
    dependency(FakeSession("session-g1"), FakeRequest("203.0.113.10"))
    # a fresh session from a different IP is unaffected by the first IP's cap
    dependency(FakeSession("session-g2"), FakeRequest("203.0.113.11"))


def test_check_ip_rate_limit_allows_calls_under_the_cap():
    for _ in range(3):
        check_ip_rate_limit("test_ip_direct", "203.0.113.20", max_calls=3, window_seconds=60)


def test_check_ip_rate_limit_blocks_once_the_cap_is_hit():
    for _ in range(2):
        check_ip_rate_limit("test_ip_direct_blocks", "203.0.113.21", max_calls=2, window_seconds=60)
    with pytest.raises(ApiError) as exc_info:
        check_ip_rate_limit("test_ip_direct_blocks", "203.0.113.21", max_calls=2, window_seconds=60)
    assert exc_info.value.status_code == 429


def test_check_ip_rate_limit_tracks_each_ip_independently():
    check_ip_rate_limit("test_ip_direct_iso", "203.0.113.22", max_calls=1, window_seconds=60)
    # a different IP is unaffected by the first IP's cap
    check_ip_rate_limit("test_ip_direct_iso", "203.0.113.23", max_calls=1, window_seconds=60)
