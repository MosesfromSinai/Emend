import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db import get_db
from api.errors import ApiError
from api.models import Application, ResumeVersion
from api.sessions import CurrentSession

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

DB = Annotated[Session, Depends(get_db)]


def _get_version(version_id: uuid.UUID, session_id: uuid.UUID, db: Session) -> ResumeVersion:
    version = db.scalars(
        select(ResumeVersion)
        .join(Application, ResumeVersion.application_id == Application.id)
        .where(ResumeVersion.id == version_id, Application.session_id == session_id)
    ).first()
    if version is None:
        # 404 for both "doesn't exist" and "not yours" — don't leak existence
        raise ApiError(404, "not_found", "Artifact not found")
    return version


@router.get("/{version_id}.pdf")
def get_pdf(version_id: uuid.UUID, session: CurrentSession, db: DB) -> FileResponse:
    version = _get_version(version_id, session.id, db)
    if not version.pdf_path or not Path(version.pdf_path).is_file():
        raise ApiError(404, "not_found", "PDF artifact is no longer available")
    return FileResponse(
        version.pdf_path, media_type="application/pdf", filename="resume.pdf"
    )


@router.get("/{version_id}.tex")
def get_tex(version_id: uuid.UUID, session: CurrentSession, db: DB) -> Response:
    version = _get_version(version_id, session.id, db)
    # served verbatim: the % grounded: receipt comments are the product
    return Response(
        content=version.tex,
        media_type="application/x-tex",
        headers={"Content-Disposition": 'attachment; filename="resume.tex"'},
    )
