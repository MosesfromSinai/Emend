import uuid

from api.config import settings


def test_cookie_issued_on_first_visit(client, master):
    r = client.put("/resumes/master", json=master.model_dump())
    assert r.status_code == 200
    cookie = r.headers.get("set-cookie", "")
    assert settings.session_cookie_name in cookie
    assert "HttpOnly" in cookie
    uuid.UUID(client.cookies[settings.session_cookie_name])  # value is a UUID


def test_session_persists_across_requests(client, master):
    client.put("/resumes/master", json=master.model_dump())
    first = client.cookies[settings.session_cookie_name]
    r = client.get("/resumes/master")
    assert r.status_code == 200
    assert client.cookies[settings.session_cookie_name] == first


def test_sessions_are_isolated(client, other_client, master):
    client.put("/resumes/master", json=master.model_dump())
    r = other_client.get("/resumes/master")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "no_master_resume"


def test_stale_cookie_gets_fresh_session(client, master):
    client.cookies.set(settings.session_cookie_name, str(uuid.uuid4()))
    r = client.get("/resumes/master")
    # unknown session id: a new session is created rather than an error
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "no_master_resume"


def test_garbage_cookie_gets_fresh_session(client):
    client.cookies.set(settings.session_cookie_name, "not-a-uuid")
    r = client.get("/resumes/master")
    assert r.status_code == 404


def test_new_session_creation_is_rate_limited_per_ip(client):
    # minting a new session is a DB write reachable from any route with no
    # cookie -- a script churning cookies (dropping it between requests, so
    # every call looks like a brand-new visitor) must not grow the sessions
    # table without bound, regardless of whether the endpoint it's hitting
    # has its own rate limit.
    for _ in range(60):
        client.cookies.clear()
        r = client.get("/resumes/master")
        assert r.status_code == 404  # no master resume yet -- a normal response
    client.cookies.clear()
    r = client.get("/resumes/master")
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited"


def test_new_session_cookie_sticks_even_when_the_request_fails(client):
    # A cookie-less visitor's very first request can easily be one that
    # errors (e.g. no master resume yet) -- the session created for them
    # must still reach the browser, not get silently dropped because the
    # response happened to be a 404 instead of a 200.
    r = client.get("/resumes/master")
    assert r.status_code == 404
    cookie = r.headers.get("set-cookie", "")
    assert settings.session_cookie_name in cookie
    uuid.UUID(client.cookies[settings.session_cookie_name])
