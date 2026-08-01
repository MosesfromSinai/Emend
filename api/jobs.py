"""The background task behind POST /applications.

Failure contract (docs/integration-guide.md §5): any stage that fails sets
status=failed with a human-readable error — compile failures carry the
Tectonic log verbatim. Never a stuck `running`, never a silent failure.
"""

import logging
import shutil
import uuid
from pathlib import Path

from api import core_bridge, db
from api.config import settings
from api.models import Application, MasterResumeRow, ResumeVersion
from core.schemas import MasterResume, Report

logger = logging.getLogger("emend.jobs")


def run_application(application_id: uuid.UUID) -> None:
    session = db.SessionLocal()
    try:
        app_row = session.get(Application, application_id)
        if app_row is None:
            logger.error("application %s vanished before the task ran", application_id)
            return
        app_row.status = "running"
        session.commit()
        try:
            _run(session, app_row)
        except Exception as e:
            logger.exception("application %s failed", application_id)
            # a mid-run DB error leaves the transaction aborted; committing
            # the failure status without clearing it first would raise again
            # and strand the row at status=running forever.
            session.rollback()
            app_row.status = "failed"
            app_row.error = f"{type(e).__name__}: {e}"
            session.commit()
    finally:
        session.close()


def _run(session, app_row: Application) -> None:
    master_row = (
        session.query(MasterResumeRow)
        .filter(MasterResumeRow.session_id == app_row.session_id)
        .first()
    )
    if master_row is None:
        app_row.status = "failed"
        app_row.error = "No confirmed master resume for this session"
        session.commit()
        return
    master = MasterResume.model_validate(master_row.data)

    tailored = None
    report: Report | None = None
    if app_row.jd_text is not None:
        jd = core_bridge.parse_jd(app_row.jd_text)
        score, matched, missing = core_bridge.keyword_match(jd, master)
        app_row.match_score = score
        app_row.matched_keywords = matched
        app_row.missing_keywords = missing
        session.commit()
        tailored = core_bridge.tailor(master, jd)
        report = core_bridge.validate(master, tailored, score, matched, missing)

    try:
        tex, pdf_path, log = core_bridge.render_and_compile(master, tailored)
    except ValueError as e:
        # tailored output referenced unknown fact ids — a grounding failure
        app_row.status = "failed"
        app_row.error = str(e)
        session.commit()
        return
    if not pdf_path:
        app_row.status = "failed"
        app_row.error = log
        session.commit()
        return

    version = ResumeVersion(
        application_id=app_row.id,
        tex=tex,  # verbatim — the % grounded: receipts are the product
        pdf_path="",
        report=report.model_dump() if report is not None else None,
    )
    session.add(version)
    session.flush()  # assign version.id before naming the artifact

    artifacts = Path(settings.artifacts_dir)
    artifacts.mkdir(parents=True, exist_ok=True)
    dest = artifacts / f"{version.id}.pdf"
    shutil.copyfile(pdf_path, dest)  # source lives in latex's temp dir
    version.pdf_path = str(dest)

    app_row.status = "done"
    session.commit()
