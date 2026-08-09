import uuid
from pathlib import Path

from api.tests.conftest import FAKE_TEX
from api.tests.test_applications import confirm_master


def _make_version(client, master):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]
    return client.get(f"/applications/{app_id}").json()["version"]


def test_pdf_download(client, master, pipeline):  # noqa: F811
    version = _make_version(client, master)
    r = client.get(version["pdf_url"])
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content == b"%PDF-1.4 fake"


def test_tex_download_verbatim(client, master, pipeline):  # noqa: F811
    version = _make_version(client, master)
    r = client.get(version["tex_url"])
    assert r.status_code == 200
    assert r.text == FAKE_TEX
    assert "% grounded:" in r.text
    assert 'filename="resume.tex"' in r.headers["content-disposition"]


def test_artifacts_are_session_scoped(client, other_client, master, pipeline):  # noqa: F811
    version = _make_version(client, master)
    for url in (version["pdf_url"], version["tex_url"]):
        assert other_client.get(url).status_code == 404
        assert other_client.get(url).json()["error"]["code"] == "not_found"


def test_missing_artifact_404(client, master, pipeline):  # noqa: F811
    version = _make_version(client, master)
    assert client.get(f"/artifacts/{uuid.uuid4()}.pdf").status_code == 404
    # deleted file on disk -> clean 404, not a 500
    from api.config import settings

    (Path(settings.artifacts_dir) / f"{version['id']}.pdf").unlink()
    assert client.get(version["pdf_url"]).status_code == 404
