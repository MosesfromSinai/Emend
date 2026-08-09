from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api import core_bridge
from api.db import get_db
from api.errors import ApiError
from api.rate_limit import rate_limit
from api.routers.applications import _load_master
from api.schemas import JdPreviewRequest, JdPreviewResponse
from api.sessions import CurrentSession

router = APIRouter(prefix="/jd", tags=["jd"])

DB = Annotated[Session, Depends(get_db)]


@router.post(
    "/preview",
    response_model=JdPreviewResponse,
    # a debounced live score card fires often during normal typing, so this
    # ceiling is much higher than the tailor/import endpoints above -- it's
    # here to stop scripted abuse of the URL-fetch path, not real usage
    dependencies=[Depends(rate_limit("jd_preview", max_calls=120, window_seconds=3600))],
)
def preview_jd(body: JdPreviewRequest, session: CurrentSession, db: DB) -> JdPreviewResponse:
    """Score a posting against the confirmed master resume -- no tailor call,
    just parse_jd + keyword_match, for the Tailor screen's live score card."""
    master = _load_master(session, db)
    if body.jd_url is not None:
        try:
            jd_text = core_bridge.fetch_jd_text(body.jd_url)
        except httpx.HTTPError as e:
            raise ApiError(422, "jd_fetch_failed", f"Could not fetch job posting URL: {e}") from e
        except core_bridge.JdUrlBlockedError as e:
            raise ApiError(422, "jd_url_blocked", str(e)) from e
    else:
        jd_text = body.jd_text

    try:
        jd = core_bridge.parse_jd(jd_text)
    except ValueError as e:
        raise ApiError(422, "jd_unscoreable", str(e)) from e
    score, matched, missing = core_bridge.keyword_match(jd, master)
    return JdPreviewResponse(
        score=score,
        matched_keywords=matched,
        missing_keywords=missing,
        resolved_jd_text=jd_text,
    )
