"""Engine, session factory, and the request-scoped DB dependency.

Tests replace `SessionLocal` (and `engine`) with an SQLite-backed factory;
always reference them as module attributes (`db.SessionLocal`), never import
the objects directly into another module's namespace.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from api.config import settings


class Base(DeclarativeBase):
    pass


# pool_pre_ping: check a pooled connection is still alive before handing it
# out. Without it, a connection that went stale while idle (DB restart, host
# sleep, idle-connection timeout) surfaces as an opaque 500 on whatever
# request happens to draw it next -- indistinguishable from a real failure,
# and "just retry" (reload) is exactly what clears it, since SQLAlchemy
# discards the dead connection and the retry gets a fresh one either way.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
