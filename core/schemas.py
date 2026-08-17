"""Team-wide data contracts. Change only via a `contract` PR approved by all four.

Fact-id format (`<ENTITY>-<NN>`) is a cross-workflow surface, not an internal
detail: the ids appear verbatim in Workflow C's `% grounded:` receipts in the
rendered `.tex` and in Workflow D's fact-tag badges. Keep the charset to
uppercase letters, digits, and a single hyphen — the render layer escapes and
whitespace-collapses anything stranger, which would break the receipts.

- Section id (`Experience.id`, `Project.id`): uppercase letters/digits, no
  hyphen — `GA`, `ACM`, `NASA`. Unique across the master resume.
- Fact id (`Fact.id`): its section id, a hyphen, then two digits — `GA-01`,
  `ACM-02`. Numbered from 01 within each section and unique resume-wide.
- `structure_resume` assigns these and they are stable within a master-resume
  version. `TailoredBullet.source_fact_ids` may only cite ids belonging to its
  own section.

Ratified decisions (integration-guide.md §8):
- `JDExtract.hard_skills` / `soft_requirements` / `responsibilities` and
  `Report.matched_keywords` / `missing_keywords` are `list[str]`. Accepted as
  proposed by Workflow C; B and D build against it.
- `Project` carries no date fields. Accepted: project dates are frequently
  ambiguous and the fact list already carries any timeframe worth showing.
  The template's empty project date slot is intentional.
"""

import re

from pydantic import BaseModel, Field, field_validator, model_validator

from core.config import max_input_chars

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
    # MasterResume.fact_lookup() also catches a duplicate, but only lazily,
    # whenever something downstream happens to call it -- a raw ValueError
    # far from the actual input boundary instead of a clean validation
    # error right here at construction time.
    seen: set[str] = set()
    for fact in facts:
        if fact.id in seen:
            raise ValueError(f"duplicate fact id within section {section_id!r}: {fact.id}")
        seen.add(fact.id)


class Fact(BaseModel):
    id: str
    # PUT /resumes/master accepts a MasterResume straight from the client --
    # this field has no upstream cap of its own the way LLM/parsed text does,
    # so without one here a client could submit an arbitrarily long bullet
    # (bounded only by the API's overall ~5MB body-size cap).
    text: str = Field(max_length=max_input_chars())

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


# A user-named section for content that doesn't fit Education/Experience/
# Projects/Skills -- "Research Experience", "Certifications", "Volunteer
# Work". Deliberately never AI-tailored: an entry's facts always render as
# literal confirmed text, the same way Education already does today, so it
# carries none of the grounding/judging machinery Experience/Project do.
# `facts` is still a `list[Fact]` (not plain strings) so the existing
# fact-editing UI and JD keyword matching (`fact_lookup`) work unchanged.
class CustomEntry(BaseModel):
    id: str
    title: str
    subtitle: str = ""
    location: str = ""
    start: str = ""
    end: str = ""
    facts: list[Fact] = []

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_section_id(value)

    @model_validator(mode="after")
    def validate_fact_prefixes(self) -> "CustomEntry":
        _validate_fact_prefix(self.id, self.facts)
        return self


_RESERVED_SECTION_KEYS = {"EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS"}


class CustomSection(BaseModel):
    key: str  # internal id for section_order/text_overrides -- never shown to the user
    heading: str  # the user's own label, e.g. "Research Experience"
    entries: list[CustomEntry] = []


class MasterResume(BaseModel):
    name: str
    email: str
    phone: str
    links: list[str]
    education: list[Education]
    experiences: list[Experience]
    projects: list[Project]
    skills: dict[str, list[str]]
    custom_sections: list[CustomSection] = []

    def _custom_entries(self) -> list[CustomEntry]:
        return [entry for section in self.custom_sections for entry in section.entries]

    @model_validator(mode="after")
    def validate_unique_section_ids(self) -> "MasterResume":
        seen: set[str] = set()
        for section in [*self.experiences, *self.projects, *self._custom_entries()]:
            if section.id in seen:
                raise ValueError(f"duplicate section id: {section.id}")
            seen.add(section.id)
        return self

    @model_validator(mode="after")
    def validate_unique_custom_section_keys(self) -> "MasterResume":
        seen: set[str] = set(_RESERVED_SECTION_KEYS)
        for section in self.custom_sections:
            if section.key in seen:
                raise ValueError(f"duplicate or reserved section key: {section.key}")
            seen.add(section.key)
        return self

    def fact_lookup(self) -> dict[str, Fact]:
        """Return every confirmed fact keyed by its id."""
        facts: dict[str, Fact] = {}
        for section in [*self.experiences, *self.projects, *self._custom_entries()]:
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
    source_url: str | None = None


class TailoredBullet(BaseModel):
    # 3 independent rewrites of the same cited fact(s), not 3 different
    # claims -- Export lets the user pick which one ships.
    variants: list[str]
    source_fact_ids: list[str]

    @model_validator(mode="after")
    def validate_unique_source_fact_ids(self) -> "TailoredBullet":
        if len(self.source_fact_ids) != len(set(self.source_fact_ids)):
            raise ValueError("source_fact_ids must be unique")
        return self

    @field_validator("variants")
    @classmethod
    def validate_three_variants(cls, value: list[str]) -> list[str]:
        if len(value) != 3 or any(not v.strip() for v in value):
            raise ValueError("variants must be exactly 3 non-empty rewrites")
        return value


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
    # ids the bullet cites, so the provenance panel can show source facts
    # without parsing `% grounded:` comments out of the tex (default keeps
    # rows written before this field existed loading cleanly)
    source_fact_ids: list[str] = []


class Report(BaseModel):
    match_score: float
    matched_keywords: list[str]
    missing_keywords: list[str]
    grounding_ok: bool
    verdicts: list[BulletVerdict]
