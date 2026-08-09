from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from api import core_bridge
from api.core_bridge import CoreUnavailableError
from api.db import get_db
from api.errors import ApiError
from api.models import MasterResumeRow
from api.rate_limit import rate_limit
from api.schemas import ImportRequest
from api.sessions import CurrentSession
from core.schemas import MasterResume

router = APIRouter(prefix="/resumes", tags=["resumes"])

DB = Annotated[Session, Depends(get_db)]


async def _resume_text_from_request(request: Request) -> str:
    """Pull resume text out of either a JSON {text} body or a multipart PDF.

    One endpoint, two shapes (per the brief's documented contract) — FastAPI
    can't bind a single handler's parameters to both at once, so the two
    paths are told apart by content-type and parsed by hand.
    """
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise ApiError(422, "validation_error", "multipart import requires a 'file' field")
        data = await upload.read()
        return core_bridge.pdf_to_text(data)
    try:
        body = ImportRequest.model_validate_json(await request.body())
    except ValidationError as e:
        raise ApiError(422, "validation_error", "Request validation failed") from e
    return body.text


@router.post(
    "/import",
    response_model=MasterResume,
    dependencies=[Depends(rate_limit("resumes_import", max_calls=20, window_seconds=3600))],
)
async def import_resume(request: Request, session: CurrentSession) -> MasterResume:
    """Propose a fact schema from pasted text or an uploaded PDF. Nothing is
    saved — the user confirms (and edits) before PUT /resumes/master persists it."""
    try:
        text = await _resume_text_from_request(request)
        return core_bridge.structure_resume(text)
    except CoreUnavailableError as e:
        raise ApiError(503, "core_unavailable", str(e)) from e
    except ValueError as e:
        # core rejected the text (e.g. invalid fenced JSON, unreadable PDF)
        raise ApiError(422, "unstructurable_resume", str(e)) from e
    except RuntimeError as e:
        # real mode without a key/package must not surface as a bare 500
        raise ApiError(503, "pipeline_unavailable", str(e)) from e


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
        raise ApiError(
            404, "no_master_resume", "No confirmed master resume for this session"
        )
    return MasterResume.model_validate(row.data)
