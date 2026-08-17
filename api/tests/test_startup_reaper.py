from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from api.main import create_app
from api.models import Application, SessionRow


def test_startup_marks_stuck_applications_failed(db_engine):
    # BackgroundTasks run in-process -- a redeploy or crash mid-job leaves
    # an Application permanently stuck at status="running"/"queued" forever,
    # with no recovery path but starting a brand-new application. A fresh
    # process finding a row already in that state can only mean a previous
    # process died mid-job, so it's reaped at startup.
    Session = sessionmaker(bind=db_engine, expire_on_commit=False)
    setup = Session()
    session_row = SessionRow()
    setup.add(session_row)
    setup.flush()
    running = Application(session_id=session_row.id, mode="refactor", status="running")
    queued = Application(session_id=session_row.id, mode="refactor", status="queued")
    done = Application(session_id=session_row.id, mode="refactor", status="done")
    setup.add_all([running, queued, done])
    setup.commit()
    running_id, queued_id, done_id = running.id, queued.id, done.id
    setup.close()

    with TestClient(create_app()):
        pass  # lifespan startup runs (and shuts down) here

    check = Session()
    assert check.get(Application, running_id).status == "failed"
    assert check.get(Application, queued_id).status == "failed"
    assert check.get(Application, done_id).status == "done"  # untouched
    assert "restart" in check.get(Application, running_id).error.lower()
