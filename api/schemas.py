"""Request/response models for the REST surface.

The OpenAPI spec generated from these is Workflow D's contract; response
shapes reuse the team contract models from core.schemas verbatim.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from api.config import settings
from core.schemas import Report

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
