"""The background task behind POST /applications.

Failure contract (docs/integration-guide.md §5): any stage that fails sets
status=failed with a human-readable error — compile failures carry the
Tectonic log verbatim. Never a stuck `running`, never a silent failure.
"""

import logging
import shutil
import uuid
from pathlib import Path

import httpx

from api import core_bridge, db
from api.config import settings
from api.models import Application, MasterResumeRow, ResumeVersion
from core.schemas import MasterResume, Report
from core.validation import GroundingError

logger = logging.getLogger("emend.jobs")


def _fact_text_map(master: MasterResume) -> dict[str, str]:
    """Flat fact id -> text snapshot of a master resume. Fact ids are
    assigned positionally (core.pipeline._assign_ids) and are only stable
    for the master resume they were assigned from, so this must be captured
    at generation time and frozen onto the version -- never recomputed from
    whatever the master resume looks like later."""
    text_by_id: dict[str, str] = {}
    for exp in master.experiences:
        for fact in exp.facts:
            text_by_id[fact.id] = fact.text
    for proj in master.projects:
        for fact in proj.facts:
            text_by_id[fact.id] = fact.text
    return text_by_id


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

    jd_text: str | None = None
    if app_row.jd_url is not None:
        try:
            jd_text = core_bridge.fetch_jd_text(app_row.jd_url)
        except httpx.HTTPError as e:
            app_row.status = "failed"
            app_row.error = f"Could not fetch job posting URL: {e}"
            session.commit()
            return
        except core_bridge.JdUrlBlockedError as e:
            app_row.status = "failed"
            app_row.error = str(e)
            session.commit()
            return
    elif app_row.jd_text is not None:
        jd_text = app_row.jd_text

    tailored = None
    report: Report | None = None
    if jd_text is not None:
        try:
            jd = core_bridge.parse_jd(jd_text)
        except ValueError as e:
            # Same friendly wording as /jd/preview (api/routers/jd.py) --
            # left unguarded here, this fell through to run_application's
            # generic `except Exception` below and landed in app_row.error
            # as a raw "ValueError: ..." string instead.
            app_row.status = "failed"
            app_row.error = str(e)
            session.commit()
            return
        score, matched, missing = core_bridge.keyword_match(jd, master)
        app_row.match_score = score
        app_row.matched_keywords = matched
        app_row.missing_keywords = missing
        session.commit()
        try:
            tailored = core_bridge.tailor(master, jd)
        except GroundingError:
            app_row.status = "failed"
            app_row.error = (
                "We couldn't produce a rewrite that passed our fact-check after "
                "a few tries. This can happen with some postings -- try tailoring "
                "again, or paste the job description text directly if you used a link."
            )
            session.commit()
            return
        report = core_bridge.validate(master, tailored, score, matched, missing)
    elif app_row.mode == "polish":
        try:
            tailored = core_bridge.polish(master)
        except GroundingError:
            app_row.status = "failed"
            app_row.error = (
                "We couldn't produce a rewrite that passed our fact-check after "
                "a few tries. Try again in a moment."
            )
            session.commit()
            return
        report = core_bridge.validate(master, tailored, 0.0, [], [])
    else:
        # No JD doesn't mean no editing -- wrap the confirmed facts the same
        # way a tailored resume is wrapped, so Export's per-line edit
        # controls work here too. render_tex output is unchanged either way
        # (verified: identical tex for tailored=None vs tailored=refactor(master)
        # on the same master); this only adds the ability to edit a line.
        tailored = core_bridge.refactor(master)

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
        # the 3-variants-per-bullet resume, so Export can re-render with a
        # different one picked -- None in refactor mode, nothing to cycle
        tailored=tailored.model_dump() if tailored is not None else None,
        # frozen snapshot of the master facts this version was generated
        # from -- see _fact_text_map for why this can't be recomputed later
        source_facts=_fact_text_map(master),
    )
    session.add(version)
    session.flush()  # assign version.id before naming the artifact

    artifacts = Path(settings.artifacts_dir)
    artifacts.mkdir(parents=True, exist_ok=True)
    dest = artifacts / f"{version.id}.pdf"
    shutil.copyfile(pdf_path, dest)  # source lives in latex's temp dir
    # compile_tex() hands back a freshly minted temp dir it never cleans up
    # itself (only the compile *scratch* dir is a context manager) -- every
    # application run leaks one unless the caller who copied the PDF out
    # removes it.
    shutil.rmtree(Path(pdf_path).parent, ignore_errors=True)
    version.pdf_path = str(dest)

    app_row.status = "done"
    session.commit()
