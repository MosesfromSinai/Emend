from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api import core_bridge
from api.core_bridge import CoreUnavailableError
from api.db import get_db
from api.errors import ApiError
from api.models import MasterResumeRow
from api.schemas import ImportRequest
from api.sessions import CurrentSession
from core.schemas import MasterResume

router = APIRouter(prefix="/resumes", tags=["resumes"])

DB = Annotated[Session, Depends(get_db)]


@router.post("/import", response_model=MasterResume)
def import_resume(body: ImportRequest, session: CurrentSession) -> MasterResume:
    """Propose a fact schema from pasted text. Nothing is saved — the user
    confirms (and edits) before PUT /resumes/master persists it."""
    try:
        return core_bridge.structure_resume(body.text)
    except CoreUnavailableError as e:
        raise ApiError(503, "core_unavailable", str(e)) from e


@router.put("/master", response_model=MasterResume)
def save_master(body: MasterResume, session: CurrentSession, db: DB) -> MasterResume:
    row = db.scalars(
        select(MasterResumeRow).where(MasterResumeRow.session_id == session.id)
    ).first()
    if row is None:
        row = MasterResumeRow(session_id=session.id, data=body.model_dump())
        db.add(row)
    else:
        row.data = body.model_dump()
    db.commit()
    return body


@router.get("/master", response_model=MasterResume)
def get_master(session: CurrentSession, db: DB) -> MasterResume:
    row = db.scalars(
        select(MasterResumeRow).where(MasterResumeRow.session_id == session.id)
    ).first()
    if row is None:
        raise ApiError(404, "no_master_resume", "No confirmed master resume for this session")
    return MasterResume.model_validate(row.data)
