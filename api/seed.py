"""Seed the local DB for an instant demo: one session + confirmed sample
resume, and a sample posting printed for the tailor flow.

    python -m api.seed          (or from compose: docker compose exec api python -m api.seed)
"""

from api import db
from api.config import settings
from api.models import MasterResumeRow, SessionRow
from api.seed_data import SAMPLE_MASTER, SAMPLE_POSTING


def seed() -> None:
    session = db.SessionLocal()
    try:
        row = SessionRow()
        session.add(row)
        session.flush()
        session.add(MasterResumeRow(session_id=row.id, data=SAMPLE_MASTER.model_dump()))
        session.commit()
        cookie = f"{settings.session_cookie_name}={row.id}"
        print("Seeded session with a confirmed master resume.")
        print(f"  cookie: {cookie}")
        print("\nRefactor mode:")
        print(
            f'  curl -s -X POST localhost:8000/applications -b "{cookie}" '
            "-H 'content-type: application/json' -d '{}'"
        )
        print("\nTailor mode — use this sample posting as jd_text:")
        print(SAMPLE_POSTING)
    finally:
        session.close()


if __name__ == "__main__":
    seed()
