"""Deterministic mock pipeline helpers."""

import json
import os
import re

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

MOCK_ENABLED = os.getenv("MOCK", "1").lower() not in {"0", "false", "no"}
JD_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#]*(?:[.-][A-Za-z0-9+#]+)*")


def _require_mock() -> None:
    if not MOCK_ENABLED:
        raise RuntimeError("MOCK=0 real LLM pipeline is not implemented yet")


def structure_resume(text: str) -> MasterResume:
    """Mock structuring: accept an already structured MasterResume JSON blob."""
    _require_mock()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("MOCK structure_resume expects MasterResume JSON") from exc
    return MasterResume(**data)


def parse_jd(text: str) -> JDExtract:
    """Mock JD parsing: accept JSON or derive keywords from plain JD text."""
    _require_mock()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        keywords = list(dict.fromkeys(JD_TOKEN_PATTERN.findall(text)))
        return JDExtract(
            company="",
            title="",
            hard_skills=[],
            soft_requirements=[],
            responsibilities=[text.strip()] if text.strip() else [],
            keywords=keywords,
        )
    return JDExtract(**data)


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
    _require_mock()
    return TailoredResume(
        summary_of_strategy="Mock refactor: preserve confirmed facts without rewriting.",
        experiences=[experience_section(experience) for experience in master.experiences],
        projects=[project_section(project) for project in master.projects],
        skills=master.skills,
    )


def mock_refactor_result(master: MasterResume) -> tuple[TailoredResume, Report]:
    """Return grounded mock refactor output plus its validation report."""
    tailored = mock_refactor_resume(master)
    validate_grounding(master, tailored)
    return tailored, build_grounding_report(tailored, 0.0, [], [])


def refactor(master: MasterResume) -> TailoredResume:
    """Public refactor entrypoint; MOCK mode preserves confirmed facts."""
    tailored, _report = mock_refactor_result(master)
    return tailored


def mock_tailor_resume(master: MasterResume, jd: JDExtract) -> tuple[TailoredResume, Report]:
    """Return grounded mock tailoring plus its validation report."""
    tailored = mock_refactor_resume(master)
    score, matched, missing = keyword_match(jd, master)
    tailored.summary_of_strategy = "Mock tailor: preserve facts and report keyword overlap."
    validate_grounding(master, tailored)
    return tailored, build_grounding_report(tailored, score, matched, missing)


def tailor(master: MasterResume, jd: JDExtract) -> TailoredResume:
    """Public tailor entrypoint; MOCK mode preserves confirmed facts."""
    tailored, _report = mock_tailor_resume(master, jd)
    return tailored
