"""Request/response models for the REST surface.

The OpenAPI spec generated from these is Workflow D's contract; response
shapes reuse the team contract models from core.schemas verbatim.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from api.config import settings
from core.schemas import Report, TailoredResume

TextField = Field(min_length=1, max_length=settings.max_text_chars)


class ImportRequest(BaseModel):
    text: str = TextField


class CreateApplicationRequest(BaseModel):
    jd_text: str | None = Field(
        default=None, min_length=1, max_length=settings.max_text_chars
    )
    jd_url: str | None = Field(default=None, min_length=1, max_length=2048)

    @model_validator(mode="after")
    def validate_jd_text_and_url_are_exclusive(self) -> "CreateApplicationRequest":
        if self.jd_text is not None and self.jd_url is not None:
            raise ValueError("jd_text and jd_url cannot both be set")
        return self


class CreateApplicationResponse(BaseModel):
    id: uuid.UUID


class VersionOut(BaseModel):
    id: uuid.UUID
    tex: str
    report: Report | None
    # the 3-variants-per-bullet resume Export cycles through -- None in
    # refactor mode, nothing tailored to pick between
    tailored: TailoredResume | None
    # fact id -> text snapshot of the master resume as it was when this
    # version was generated -- "view my original" must read from here, not
    # from a fresh GET of the (possibly since-edited) master resume, or a
    # stale/reused fact id can show an AI rewrite as the user's own wording
    source_facts: dict[str, str] = {}
    pdf_url: str
    tex_url: str
    created_at: datetime


class ApplicationOut(BaseModel):
    id: uuid.UUID
    mode: str
    status: str
    match_score: float | None
    matched_keywords: list[str] | None
    missing_keywords: list[str] | None
    error: str | None
    created_at: datetime
    version: VersionOut | None
    jd_source_url: str | None = None


class BulletSelection(BaseModel):
    """Which of a bullet's 3 variants renders -- keyed by fact id on the
    request. Neither field set: the first variant renders."""

    variant_idx: int | None = Field(default=None, ge=0, le=2)
    custom_text: str | None = None


class RenderRequest(BaseModel):
    selections: dict[str, BulletSelection] = {}
    # keyed by an experience/project's own id -- the full ordered list of
    # that entry's fact ids after the user's up/down moves on Export
    fact_order: dict[str, list[str]] = {}
    # the full ordered list of experience/project entry ids (ref_ids in
    # tailor mode, the entry's own id in refactor mode) after the user's
    # up/down moves on an entry's header -- None means no override
    experience_order: list[str] | None = None
    project_order: list[str] | None = None
    # the full ordered list of the four top-level section keys ("EDUCATION",
    # "EXPERIENCE", "PROJECTS", "SKILLS") after the user reorders them on
    # Export -- None or a partial/unrecognized list falls back to the
    # default relative order for whatever's missing
    section_order: list[str] | None = None
    # fact ids / entry ids the user deleted on Export -- dropped from
    # rendering entirely. Export-time only: never touches the confirmed
    # master resume or the stored tailored version, so undoing is just
    # removing an id from these lists again.
    excluded_facts: list[str] = []
    excluded_experiences: list[str] = []
    excluded_projects: list[str] = []


class RenderPreviewResponse(BaseModel):
    tex: str


class JdPreviewRequest(BaseModel):
    jd_text: str | None = Field(
        default=None, min_length=1, max_length=settings.max_text_chars
    )
    jd_url: str | None = Field(default=None, min_length=1, max_length=2048)

    @model_validator(mode="after")
    def validate_exactly_one_source(self) -> "JdPreviewRequest":
        if self.jd_text is not None and self.jd_url is not None:
            raise ValueError("jd_text and jd_url cannot both be set")
        if self.jd_text is None and self.jd_url is None:
            raise ValueError("jd_text or jd_url is required")
        return self


class JdPreviewResponse(BaseModel):
    score: float
    matched_keywords: list[str]
    missing_keywords: list[str]
    resolved_jd_text: str


class ApplicationListItem(BaseModel):
    id: uuid.UUID
    mode: str
    status: str
    match_score: float | None
    error: str | None
    created_at: datetime


class HealthOut(BaseModel):
    status: str
