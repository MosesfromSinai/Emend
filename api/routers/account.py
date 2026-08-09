"""Account-level actions. There's no signup/login in this app -- the
session cookie *is* the account -- so today this is just one endpoint:
permanently deleting everything that cookie can reach.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import settings
from api.db import get_db
from api.models import Application, MasterResumeRow
from api.sessions import CurrentSession

router = APIRouter(prefix="/account", tags=["account"])

DB = Annotated[Session, Depends(get_db)]


@router.delete("", status_code=204)
def delete_my_data(session: CurrentSession, db: DB, response: Response) -> None:
    """Delete the confirmed master resume, every application (and its
    rendered PDF on disk), and the session row itself. Irreversible --
    there is no confirmation step here; the frontend owns that before ever
    calling this.
    """
    applications = db.scalars(
        select(Application).where(Application.session_id == session.id)
    )
    for application in applications:
        for version in application.versions:
            if version.pdf_path:
                Path(version.pdf_path).unlink(missing_ok=True)
        db.delete(application)  # cascades to its ResumeVersion rows

    master_row = db.scalars(
        select(MasterResumeRow).where(MasterResumeRow.session_id == session.id)
    ).first()
    if master_row is not None:
        db.delete(master_row)

    db.delete(session)
    db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
