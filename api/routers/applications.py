import shutil
import threading
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api import core_bridge, jobs
from api.config import settings
from api.db import get_db
from api.errors import ApiError
from api.models import Application, MasterResumeRow, ResumeVersion
from api.rate_limit import rate_limit
from api.schemas import (
    ApplicationListItem,
    ApplicationOut,
    CreateApplicationRequest,
    CreateApplicationResponse,
    RenderPreviewResponse,
    RenderRequest,
    VersionOut,
)
from api.sessions import CurrentSession
from core.schemas import MasterResume, TailoredResume

router = APIRouter(prefix="/applications", tags=["applications"])

DB = Annotated[Session, Depends(get_db)]

_finalize_locks: dict[uuid.UUID, threading.Lock] = {}
_finalize_locks_guard = threading.Lock()


def _finalize_lock(application_id: uuid.UUID) -> threading.Lock:
    # Serializes concurrent finalize calls for one application so a
    # double-click/duplicate tab can't interleave one request's PDF write
    # with another's DB commit, leaving a downloaded PDF that silently
    # doesn't match the .tex shown for that version. Unlike polish, there's
    # no status field to claim atomically here -- finalize legitimately
    # re-runs on every call, so it serializes instead of rejecting.
    with _finalize_locks_guard:
        lock = _finalize_locks.get(application_id)
        if lock is None:
            lock = threading.Lock()
            _finalize_locks[application_id] = lock
        return lock


def _owned_application(application_id: uuid.UUID, session: CurrentSession, db: DB) -> Application:
    app_row = db.scalars(
        select(Application).where(
            Application.id == application_id, Application.session_id == session.id
        )
    ).first()
    if app_row is None:
        raise ApiError(404, "not_found", "Application not found")
    return app_row


def _latest_version(app_row: Application) -> ResumeVersion:
    version = next(
        iter(sorted(app_row.versions, key=lambda v: v.created_at, reverse=True)), None
    )
    if version is None:
        raise ApiError(404, "not_found", "No rendered version yet")
    return version


def _load_master(session: CurrentSession, db: DB) -> MasterResume:
    row = db.scalars(
        select(MasterResumeRow).where(MasterResumeRow.session_id == session.id)
    ).first()
    if row is None:
        raise ApiError(404, "no_master_resume", "No confirmed master resume")
    return MasterResume.model_validate(row.data)


@router.post(
    "",
    response_model=CreateApplicationResponse,
    status_code=202,
    dependencies=[Depends(rate_limit("applications", max_calls=15, window_seconds=3600))],
)
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
            409,
            "no_master_resume",
            "Confirm a master resume before creating an application",
        )
    app_row = Application(
        session_id=session.id,
        mode="refactor" if body.jd_text is None and body.jd_url is None else "tailor",
        jd_text=body.jd_text,
        jd_url=body.jd_url,
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
        tailored=_tailored_from(version),
        source_facts=version.source_facts or {},
        pdf_url=f"/artifacts/{version.id}.pdf",
        tex_url=f"/artifacts/{version.id}.tex",
        created_at=version.created_at,
    )


def _application_out(app_row: Application) -> ApplicationOut:
    version = next(
        iter(sorted(app_row.versions, key=lambda v: v.created_at, reverse=True)), None
    )
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
        jd_source_url=app_row.jd_url,
    )


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: uuid.UUID, session: CurrentSession, db: DB
) -> ApplicationOut:
    return _application_out(_owned_application(application_id, session, db))


@router.post(
    "/{application_id}/polish",
    response_model=ApplicationOut,
    status_code=202,
    dependencies=[Depends(rate_limit("applications", max_calls=15, window_seconds=3600))],
)
def polish_application(
    application_id: uuid.UUID,
    session: CurrentSession,
    db: DB,
    background: BackgroundTasks,
) -> ApplicationOut:
    """The "make this as strong as possible" upgrade, offered on Export once
    a plain formatted (no-AI) resume already exists. Re-runs generation for
    this same application in AI-polish mode -- a fresh ResumeVersion lands
    alongside the original one, and the user's structural Export edits
    (reorder, exclude, header/skills overrides) stay keyed by the same
    fact/section ids, so they still apply once it's done."""
    app_row = _owned_application(application_id, session, db)
    if app_row.mode == "tailor":
        raise ApiError(
            409, "not_polishable", "A posting-tailored resume is already an AI rewrite"
        )
    # A plain read-then-write here would let two near-simultaneous requests
    # (double-click, duplicate tab) both pass this check before either
    # commits, queuing two concurrent jobs against the same row -- same
    # race class as the master-resume save race, on a different endpoint.
    # The UPDATE's WHERE re-checks status atomically at the database, so
    # only one request's claim can ever win.
    result = db.execute(
        update(Application)
        .where(Application.id == app_row.id, Application.status.notin_(["queued", "running"]))
        .values(mode="polish", status="queued", error=None)
    )
    db.commit()
    if result.rowcount == 0:
        raise ApiError(409, "already_running", "This application is still generating")
    db.refresh(app_row)
    background.add_task(jobs.run_application, app_row.id)
    return _application_out(app_row)


def _tailored_from(version: ResumeVersion) -> TailoredResume | None:
    return TailoredResume.model_validate(version.tailored) if version.tailored else None


@router.post(
    "/{application_id}/preview",
    response_model=RenderPreviewResponse,
    dependencies=[Depends(rate_limit("applications_preview", max_calls=300, window_seconds=3600))],
)
def preview_application(
    application_id: uuid.UUID, body: RenderRequest, session: CurrentSession, db: DB
) -> RenderPreviewResponse:
    """Cheap re-render (no compile) reflecting the user's current variant
    picks -- called on every cycle/edit on Export, so the .tex pane never
    lags behind what's selected."""
    app_row = _owned_application(application_id, session, db)
    version = _latest_version(app_row)
    master = _load_master(session, db)
    selections = {k: v.model_dump(exclude_none=True) for k, v in body.selections.items()}
    try:
        tex = core_bridge.render_tex(
            master,
            _tailored_from(version),
            selections=selections,
            fact_order=body.fact_order,
            experience_order=body.experience_order,
            project_order=body.project_order,
            section_order=body.section_order,
            excluded_facts=body.excluded_facts,
            excluded_experiences=body.excluded_experiences,
            excluded_projects=body.excluded_projects,
            text_overrides=body.text_overrides,
        )
    except ValueError as e:
        raise ApiError(409, "stale_tailored_resume", str(e)) from e
    return RenderPreviewResponse(tex=tex)


@router.post(
    "/{application_id}/finalize",
    response_model=VersionOut,
    dependencies=[Depends(rate_limit("applications_finalize", max_calls=30, window_seconds=3600))],
)
def finalize_application(
    application_id: uuid.UUID, body: RenderRequest, session: CurrentSession, db: DB
) -> VersionOut:
    """Real compile with the user's final picks -- runs once, on download."""
    app_row = _owned_application(application_id, session, db)
    version = _latest_version(app_row)
    master = _load_master(session, db)
    selections = {k: v.model_dump(exclude_none=True) for k, v in body.selections.items()}
    with _finalize_lock(app_row.id):
        try:
            tex, pdf_path, log = core_bridge.render_and_compile(
                master,
                _tailored_from(version),
                selections=selections,
                fact_order=body.fact_order,
                experience_order=body.experience_order,
                project_order=body.project_order,
                section_order=body.section_order,
                excluded_facts=body.excluded_facts,
                excluded_experiences=body.excluded_experiences,
                excluded_projects=body.excluded_projects,
                text_overrides=body.text_overrides,
            )
        except ValueError as e:
            raise ApiError(409, "stale_tailored_resume", str(e)) from e
        if not pdf_path:
            raise ApiError(422, "compile_failed", log)
        version.tex = tex
        artifacts = Path(settings.artifacts_dir)
        artifacts.mkdir(parents=True, exist_ok=True)
        dest = artifacts / f"{version.id}.pdf"
        shutil.copyfile(pdf_path, dest)
        # See api/jobs.py's identical cleanup for why: compile_tex()'s
        # returned temp dir is never removed on its own.
        shutil.rmtree(Path(pdf_path).parent, ignore_errors=True)
        version.pdf_path = str(dest)
        db.commit()
    return _version_out(version)


#  A session accumulates applications indefinitely (no retention/deletion
# path but the user's own explicit DELETE /account) -- this caps the
# response instead of returning every row a long-lived session has ever
# created. Most-recent-first ordering means a session past the cap simply
# stops seeing its oldest history, not an arbitrary subset.
MAX_APPLICATIONS_LISTED = 200


@router.get("", response_model=list[ApplicationListItem])
def list_applications(session: CurrentSession, db: DB) -> list[ApplicationListItem]:
    rows = db.scalars(
        select(Application)
        .where(Application.session_id == session.id)
        .order_by(Application.created_at.desc(), Application.id)
        .limit(MAX_APPLICATIONS_LISTED)
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
