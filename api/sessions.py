"""Anonymous sessions: httpOnly cookie issued on first visit, no accounts.

`CurrentSession` is the dependency every session-scoped route takes; it
creates the session row (and sets the cookie) when the visitor is new or
presents a stale/invalid cookie.
"""

import uuid
from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from api.config import settings
from api.db import get_db
from api.models import SessionRow


def _set_cookie(response: Response, session_id: uuid.UUID) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=str(session_id),
        max_age=settings.session_cookie_max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def current_session(
    request: Request, response: Response, db: Annotated[Session, Depends(get_db)]
) -> SessionRow:
    raw = request.cookies.get(settings.session_cookie_name)
    if raw:
        try:
            session_id = uuid.UUID(raw)
        except ValueError:
            session_id = None
        if session_id is not None:
            row = db.get(SessionRow, session_id)
            if row is not None:
                return row

    row = SessionRow()
    db.add(row)
    db.commit()
    _set_cookie(response, row.id)
    return row


CurrentSession = Annotated[SessionRow, Depends(current_session)]
