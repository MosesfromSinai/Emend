import pytest

from api.core_bridge import JdUrlBlockedError, _assert_public_http_url


def test_assert_public_http_url_blocks_loopback():
    with pytest.raises(JdUrlBlockedError):
        _assert_public_http_url("http://localhost/jobs/123")
    with pytest.raises(JdUrlBlockedError):
        _assert_public_http_url("http://127.0.0.1/jobs/123")


def test_assert_public_http_url_blocks_cloud_metadata_address():
    with pytest.raises(JdUrlBlockedError):
        _assert_public_http_url("http://169.254.169.254/latest/meta-data/")


def test_assert_public_http_url_blocks_private_ranges():
    with pytest.raises(JdUrlBlockedError):
        _assert_public_http_url("http://10.0.0.5/jobs")
    with pytest.raises(JdUrlBlockedError):
        _assert_public_http_url("http://192.168.1.1/jobs")


def test_assert_public_http_url_blocks_non_http_scheme():
    with pytest.raises(JdUrlBlockedError):
        _assert_public_http_url("file:///etc/passwd")
    with pytest.raises(JdUrlBlockedError):
        _assert_public_http_url("ftp://example.com/jobs")


def test_assert_public_http_url_allows_a_real_public_address():
    # a literal public IP needs no DNS resolution and is stable to test
    # against -- this is one of Google's public DNS addresses, not a
    # network call this test depends on succeeding
    _assert_public_http_url("http://8.8.8.8/jobs")
