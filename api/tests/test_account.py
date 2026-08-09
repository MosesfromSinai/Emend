from pathlib import Path

from api.config import settings
from api.tests.test_applications import confirm_master


def test_delete_my_data_removes_everything(client, master, pipeline):
    confirm_master(client, master)
    r = client.post("/applications", json={})
    assert r.status_code == 202
    app_id = r.json()["id"]

    got = client.get(f"/applications/{app_id}").json()
    pdf_path = Path(settings.artifacts_dir) / f"{got['version']['id']}.pdf"
    assert pdf_path.is_file()

    delete_response = client.delete("/account")
    assert delete_response.status_code == 204

    # the PDF artifact on disk is gone, not just the DB rows
    assert not pdf_path.is_file()
    assert client.get("/resumes/master").status_code == 404
    assert client.get("/applications").json() == []
    assert client.get(f"/applications/{app_id}").status_code == 404


def test_delete_my_data_is_safe_with_nothing_to_delete(client):
    # a brand-new visitor who never confirmed a resume or ran a tailor
    assert client.delete("/account").status_code == 204


def test_delete_my_data_does_not_touch_another_sessions_data(
    client, other_client, master, pipeline
):
    confirm_master(client, master)
    other_client.put("/resumes/master", json=master.model_dump())

    assert client.delete("/account").status_code == 204

    assert client.get("/resumes/master").status_code == 404
    assert other_client.get("/resumes/master").status_code == 200
