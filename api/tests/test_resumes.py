import pytest

from api import core_bridge
from api.config import settings
from api.core_bridge import CoreUnavailableError
from api.tests.conftest import sample_master


@pytest.fixture()
def stub_structure(monkeypatch):
    def fake_structure_resume(text: str):
        return sample_master()

    monkeypatch.setattr(core_bridge, "structure_resume", fake_structure_resume)


def test_import_returns_proposed_schema_unsaved(client, stub_structure):
    r = client.post("/resumes/import", json={"text": "my resume text"})
    assert r.status_code == 200
    assert r.json()["name"] == "Sam Sample"
    assert r.json()["experiences"][0]["facts"][0]["id"] == "ACME-01"
    # nothing was saved: master is still absent
    assert client.get("/resumes/master").status_code == 404


def test_import_503_when_core_missing(client, monkeypatch):
    def unavailable(text: str):
        raise CoreUnavailableError("core.structure_resume is not available yet")

    monkeypatch.setattr(core_bridge, "structure_resume", unavailable)
    r = client.post("/resumes/import", json={"text": "hi"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "core_unavailable"


def test_import_text_required_and_capped(client, stub_structure):
    assert client.post("/resumes/import", json={}).status_code == 422
    assert client.post("/resumes/import", json={"text": ""}).status_code == 422
    too_long = "x" * (settings.max_text_chars + 1)
    r = client.post("/resumes/import", json={"text": too_long})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_master_round_trip_and_upsert(client, master):
    assert client.put("/resumes/master", json=master.model_dump()).status_code == 200
    got = client.get("/resumes/master")
    assert got.status_code == 200
    assert got.json() == master.model_dump()

    master.name = "Sam Updated"
    assert client.put("/resumes/master", json=master.model_dump()).status_code == 200
    assert client.get("/resumes/master").json()["name"] == "Sam Updated"


def test_master_rejects_invalid_schema(client):
    r = client.put("/resumes/master", json={"name": "no other fields"})
    assert r.status_code == 422


def test_oversized_body_rejected(client):
    huge = "x" * (settings.max_body_bytes + 1)
    r = client.post(
        "/resumes/import", content=huge, headers={"content-type": "application/json"}
    )
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"
