"""SQLAlchemy 2 models for the four contract tables (see 00-project-brief.md).

JSONB on Postgres, plain JSON elsewhere (SQLite in tests) via `with_variant`.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base

JSONVariant = JSON().with_variant(JSONB(), "postgresql")

APPLICATION_STATUSES = ("queued", "running", "done", "failed")


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MasterResumeRow(Base):
    __tablename__ = "master_resumes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    data: Mapped[dict] = mapped_column(JSONVariant, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)  # refactor | tailor
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    jd_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_keywords: Mapped[list | None] = mapped_column(JSONVariant, nullable=True)
    missing_keywords: Mapped[list | None] = mapped_column(JSONVariant, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tex: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(512), nullable=False)
    report: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    # the full TailoredResume (3 variants per bullet), not just the rendered
    # tex -- needed so Export can re-render with a different variant picked.
    # None in refactor mode, where there's nothing to cycle between.
    tailored: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    # fact id -> text snapshot of the master resume *at generation time*.
    # Fact ids are assigned positionally (core.pipeline._assign_ids) and are
    # not stable across master-resume edits, so "view my original" must read
    # from this frozen snapshot rather than the live master -- otherwise a
    # later edit can make a stale fact id collide with a different fact (or
    # vanish), silently showing an AI rewrite as the user's original wording.
    source_facts: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    # Python-side default (not server_default=func.now()) so this carries
    # real microsecond precision -- SQLite's CURRENT_TIMESTAMP is
    # second-resolution, and an application can now get two versions
    # (format, then AI-polish) within the same second. `_latest_version`'s
    # ordering must actually reflect which one is newer, not tie-break on
    # insertion order it never captured.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="versions")
