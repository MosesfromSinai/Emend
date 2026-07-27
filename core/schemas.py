"""Team-wide data contracts. Change only via a `contract` PR approved by all four."""

import re

from pydantic import BaseModel, field_validator, model_validator

FACT_ID_PATTERN = re.compile(r"^[A-Z0-9]+-\d{2}$")
SECTION_ID_PATTERN = re.compile(r"^[A-Z0-9]+$")


def _validate_section_id(value: str) -> str:
    if not SECTION_ID_PATTERN.fullmatch(value):
        raise ValueError("section id must be uppercase letters or digits")
    return value


def _validate_fact_prefix(section_id: str, facts: list["Fact"]) -> None:
    bad_ids = [fact.id for fact in facts if not fact.id.startswith(f"{section_id}-")]
    if bad_ids:
        raise ValueError(f"fact ids must start with section id: {bad_ids}")


class Fact(BaseModel):
    id: str
    text: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not FACT_ID_PATTERN.fullmatch(value):
            raise ValueError("fact id must match <ENTITY>-<NN>")
        return value


class Experience(BaseModel):
    id: str
    company: str
    title: str
    location: str
    start: str
    end: str
    facts: list[Fact]

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_section_id(value)

    @model_validator(mode="after")
    def validate_fact_prefixes(self) -> "Experience":
        _validate_fact_prefix(self.id, self.facts)
        return self


class Project(BaseModel):
    id: str
    name: str
    tech: list[str]
    facts: list[Fact]

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_section_id(value)

    @model_validator(mode="after")
    def validate_fact_prefixes(self) -> "Project":
        _validate_fact_prefix(self.id, self.facts)
        return self


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

    def fact_lookup(self) -> dict[str, Fact]:
        """Return every confirmed fact keyed by its id."""
        facts: dict[str, Fact] = {}
        for section in [*self.experiences, *self.projects]:
            for fact in section.facts:
                if fact.id in facts:
                    raise ValueError(f"duplicate fact id: {fact.id}")
                facts[fact.id] = fact
        return facts

    def all_fact_ids(self) -> set[str]:
        """Return all confirmed fact ids for grounding checks."""
        return set(self.fact_lookup())


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
