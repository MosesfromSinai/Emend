"""Anonymous sessions: httpOnly cookie issued on first visit, no accounts.

`CurrentSession` is the dependency every session-scoped route takes; it
creates the session row when the visitor is new or presents a stale/invalid
cookie. The cookie itself is set by `attach_session_cookie` in api/main.py,
not here -- a per-dependency `Response` object's headers only get merged
into the real outgoing response on the success path (FastAPI/Starlette
quirk), so setting it here would silently vanish on any request where the
route later raises (e.g. a 422 from a malformed resume paste), leaving a
brand-new visitor cookie-less and orphaning a fresh SessionRow on every
retry. Recording the new id on `request.state` instead lets a middleware
attach it to whatever response actually goes out, error or not.
"""

import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from api.config import settings
from api.db import get_db
from api.models import SessionRow


def current_session(request: Request, db: Annotated[Session, Depends(get_db)]) -> SessionRow:
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
    request.state.new_session_id = row.id
    return row


CurrentSession = Annotated[SessionRow, Depends(current_session)]
