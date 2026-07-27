from sqlalchemy import select

from api import db as db_module
from api.models import MasterResumeRow, SessionRow
from api.seed import seed
from core.schemas import MasterResume


def test_seed_creates_confirmed_master(db_engine, capsys):
    seed()
    out = capsys.readouterr().out
    assert "emend_session=" in out

    session = db_module.SessionLocal()
    try:
        rows = session.scalars(select(MasterResumeRow)).all()
        assert len(rows) == 1
        master = MasterResume.model_validate(rows[0].data)  # valid contract schema
        assert master.experiences[0].facts[0].id == "ACME-01"
        assert session.get(SessionRow, rows[0].session_id) is not None
    finally:
        session.close()
