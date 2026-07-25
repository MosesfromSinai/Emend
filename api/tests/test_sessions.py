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
