"""Deterministic mock pipeline helpers."""

from core.matching import keyword_match
from core.schemas import (
    JDExtract,
    Experience,
    MasterResume,
    Project,
    Report,
    TailoredBullet,
    TailoredResume,
    TailoredSection,
)
from core.validation import build_grounding_report, validate_grounding


def _fact_bullets(facts) -> list[TailoredBullet]:
    return [TailoredBullet(text=fact.text, source_fact_ids=[fact.id]) for fact in facts]


def experience_section(experience: Experience) -> TailoredSection:
    """Convert confirmed experience facts into grounded bullets."""
    return TailoredSection(ref_id=experience.id, bullets=_fact_bullets(experience.facts))


def project_section(project: Project) -> TailoredSection:
    """Convert confirmed project facts into grounded bullets."""
    return TailoredSection(ref_id=project.id, bullets=_fact_bullets(project.facts))


def mock_refactor_resume(master: MasterResume) -> TailoredResume:
    """Return a renderable resume using only confirmed master facts."""
    return TailoredResume(
        summary_of_strategy="Mock refactor: preserve confirmed facts without rewriting.",
        experiences=[experience_section(experience) for experience in master.experiences],
        projects=[project_section(project) for project in master.projects],
        skills=master.skills,
    )


def mock_tailor_resume(master: MasterResume, jd: JDExtract) -> tuple[TailoredResume, Report]:
    """Return grounded mock tailoring plus its validation report."""
    tailored = mock_refactor_resume(master)
    score, matched, missing = keyword_match(jd, master)
    tailored.summary_of_strategy = "Mock tailor: preserve facts and report keyword overlap."
    validate_grounding(master, tailored)
    return tailored, build_grounding_report(tailored, score, matched, missing)
