"""Request/response models for the REST surface.

The OpenAPI spec generated from these is Workflow D's contract; response
shapes reuse the team contract models from core.schemas verbatim.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from api.config import settings
from core.schemas import Report

TextField = Field(min_length=1, max_length=settings.max_text_chars)


class ImportRequest(BaseModel):
    text: str = TextField


class CreateApplicationRequest(BaseModel):
    jd_text: str | None = Field(default=None, min_length=1, max_length=settings.max_text_chars)


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


class ApplicationListItem(BaseModel):
    id: uuid.UUID
    mode: str
    status: str
    match_score: float | None
    error: str | None
    created_at: datetime


class HealthOut(BaseModel):
    status: str
