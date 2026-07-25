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


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
