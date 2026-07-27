import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api import jobs
from api.db import get_db
from api.errors import ApiError
from api.models import Application, MasterResumeRow, ResumeVersion
from api.schemas import (
    ApplicationListItem,
    ApplicationOut,
    CreateApplicationRequest,
    CreateApplicationResponse,
    VersionOut,
)
from api.sessions import CurrentSession

router = APIRouter(prefix="/applications", tags=["applications"])

DB = Annotated[Session, Depends(get_db)]


@router.post("", response_model=CreateApplicationResponse, status_code=202)
def create_application(
    body: CreateApplicationRequest,
    session: CurrentSession,
    db: DB,
    background: BackgroundTasks,
) -> CreateApplicationResponse:
    has_master = (
        db.scalars(
            select(MasterResumeRow.id).where(MasterResumeRow.session_id == session.id)
        ).first()
        is not None
    )
    if not has_master:
        raise ApiError(
            409, "no_master_resume", "Confirm a master resume before creating an application"
        )
    app_row = Application(
        session_id=session.id,
        mode="refactor" if body.jd_text is None else "tailor",
        jd_text=body.jd_text,
        status="queued",
    )
    db.add(app_row)
    db.commit()
    background.add_task(jobs.run_application, app_row.id)
    return CreateApplicationResponse(id=app_row.id)


def _version_out(version: ResumeVersion) -> VersionOut:
    return VersionOut(
        id=version.id,
        tex=version.tex,
        report=version.report,
        pdf_url=f"/artifacts/{version.id}.pdf",
        tex_url=f"/artifacts/{version.id}.tex",
        created_at=version.created_at,
    )


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: uuid.UUID, session: CurrentSession, db: DB
) -> ApplicationOut:
    app_row = db.scalars(
        select(Application).where(
            Application.id == application_id, Application.session_id == session.id
        )
    ).first()
    if app_row is None:
        raise ApiError(404, "not_found", "Application not found")
    version = next(iter(sorted(app_row.versions, key=lambda v: v.created_at, reverse=True)), None)
    return ApplicationOut(
        id=app_row.id,
        mode=app_row.mode,
        status=app_row.status,
        match_score=app_row.match_score,
        matched_keywords=app_row.matched_keywords,
        missing_keywords=app_row.missing_keywords,
        error=app_row.error,
        created_at=app_row.created_at,
        version=_version_out(version) if version is not None else None,
    )


@router.get("", response_model=list[ApplicationListItem])
def list_applications(session: CurrentSession, db: DB) -> list[ApplicationListItem]:
    rows = db.scalars(
        select(Application)
        .where(Application.session_id == session.id)
        .order_by(Application.created_at.desc(), Application.id)
    ).all()
    return [
        ApplicationListItem(
            id=r.id,
            mode=r.mode,
            status=r.status,
            match_score=r.match_score,
            error=r.error,
            created_at=r.created_at,
        )
        for r in rows
    ]
