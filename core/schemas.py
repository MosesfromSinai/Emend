"""Team-wide data contracts. Change only via a `contract` PR approved by all four."""

from pydantic import BaseModel


class Fact(BaseModel):
    id: str
    text: str


class Experience(BaseModel):
    id: str
    company: str
    title: str
    location: str
    start: str
    end: str
    facts: list[Fact]


class Project(BaseModel):
    id: str
    name: str
    tech: list[str]
    facts: list[Fact]


class Education(BaseModel):
    school: str
    degree: str
    location: str
    grad_date: str
    coursework: list[str]


class MasterResume(BaseModel):
    name: str
    email: str
    phone: str
    links: list[str]
    education: list[Education]
    experiences: list[Experience]
    projects: list[Project]
    skills: dict[str, list[str]]


class JDExtract(BaseModel):
    company: str
    title: str
    hard_skills: list[str]
    soft_requirements: list[str]
    responsibilities: list[str]
    keywords: list[str]


class TailoredBullet(BaseModel):
    text: str
    source_fact_ids: list[str]


class TailoredSection(BaseModel):
    ref_id: str
    bullets: list[TailoredBullet]


class TailoredResume(BaseModel):
    summary_of_strategy: str
    experiences: list[TailoredSection]
    projects: list[TailoredSection]
    skills: dict[str, list[str]]


class BulletVerdict(BaseModel):
    bullet: str
    supported: bool
    reason: str


class Report(BaseModel):
    match_score: float
    matched_keywords: list[str]
    missing_keywords: list[str]
    grounding_ok: bool
    verdicts: list[BulletVerdict]
