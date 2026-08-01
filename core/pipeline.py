"""The core pipeline: deterministic under MOCK=1, real Anthropic calls under MOCK=0.

Both modes return the same Pydantic types and both pass generated content
through `validate_grounding` before returning it, so the no-invented-claims
guarantee does not depend on which mode is running.
"""

import json
import re
from typing import Any

from core.config import mock_enabled
from core.llm import FAST_MODEL, TAILOR_MODEL, cacheable_system, structured_call
from core.matching import keyword_match
from core.prompts import PARSE_JD_SYSTEM, STRUCTURE_SYSTEM, TAILOR_SYSTEM
from core.schemas import (
    Experience,
    JDExtract,
    MasterResume,
    Project,
    Report,
    TailoredBullet,
    TailoredResume,
    TailoredSection,
)
from core.validation import build_grounding_report, judge_bullets, validate_grounding

JD_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#]*(?:[.-][A-Za-z0-9+#]+)*")
JD_STOP_WORDS = {"and", "for", "the", "to", "using", "with"}
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"\(?\+?\d[\d\s().-]{7,}\d")
LINK_PATTERN = re.compile(r"(?:https?://|www\.|linkedin\.com/|github\.com/)\S+")
BULLET_PATTERN = re.compile(r"^[•\-*·]+\s*")
MAX_FACTS_PER_SECTION = 99  # fact ids carry a two-digit suffix


def _json_object_text(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return text
    return text[start : end + 1]


def _section_id(title: str, used: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9]", "", title).upper()[:4] or "SEC"
    section_id = base
    suffix = 2
    while section_id in used:
        section_id = f"{base}{suffix}"
        suffix += 1
    used.add(section_id)
    return section_id


def _text_master_resume(text: str) -> MasterResume:
    """Deterministic fallback: turn pasted plain text into one fact per line.

    Each blank-line-separated block becomes an experience whose first line is
    the heading; the remaining lines become atomic facts. Not smart, but valid
    and stable, so the confirmation screen and the rest of the pipeline work
    without an API key.
    """
    lines = [line.strip() for line in text.splitlines()]
    name = next((line for line in lines if line), "Unknown")
    email = match.group(0) if (match := EMAIL_PATTERN.search(text)) else ""
    phone = match.group(0).strip() if (match := PHONE_PATTERN.search(text)) else ""
    links = list(dict.fromkeys(link.rstrip(".,;|") for link in LINK_PATTERN.findall(text)))

    contact_lines = {name}
    experiences = []
    used_ids: set[str] = set()
    for block in re.split(r"\n\s*\n", text.strip()):
        block_lines = [line.strip() for line in block.splitlines() if line.strip()]
        facts = [
            BULLET_PATTERN.sub("", line)
            for line in block_lines[1:]
            if line not in contact_lines and not EMAIL_PATTERN.search(line)
        ][:MAX_FACTS_PER_SECTION]
        if not facts:
            continue
        section_id = _section_id(block_lines[0], used_ids)
        experiences.append(
            Experience(
                id=section_id,
                company=block_lines[0],
                title="",
                location="",
                start="",
                end="",
                facts=[
                    Fact(id=f"{section_id}-{index:02d}", text=fact)
                    for index, fact in enumerate(facts, 1)
                ],
            )
        )
    return MasterResume(
        name=name,
        email=email,
        phone=phone,
        links=links,
        education=[],
        experiences=experiences,
        projects=[],
        skills={},
    )


def _mock_structure_resume(text: str) -> MasterResume:
    """Mock structuring: MasterResume JSON fast path, plain-text fallback."""
    json_text = _json_object_text(text)
    is_json_hint = "```json" in text.lower()
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        if is_json_hint:
            raise ValueError("MOCK structure_resume found invalid MasterResume JSON") from exc
        return _text_master_resume(text)
    return MasterResume(**data)


def structure_resume(text: str, *, client: Any | None = None) -> MasterResume:
    """Turn pasted resume text into a confirmed-fact schema."""
    if mock_enabled():
        return _mock_structure_resume(text)
    return structured_call(
        FAST_MODEL,
        cacheable_system(STRUCTURE_SYSTEM),
        f"Resume text:\n\n{text}",
        MasterResume,
        client=client,
    )


def parse_jd(text: str, *, client: Any | None = None) -> JDExtract:
    """Extract structure from a job posting."""
    if not mock_enabled():
        return structured_call(
            FAST_MODEL,
            cacheable_system(PARSE_JD_SYSTEM),
            f"Job posting:\n\n{text}",
            JDExtract,
            client=client,
        )
    json_text = _json_object_text(text)
    is_json_hint = "```json" in text.lower()
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        if is_json_hint or json_text != text:
            raise ValueError("MOCK parse_jd found invalid JDExtract JSON") from exc
        keywords = [
            token
            for token in dict.fromkeys(JD_TOKEN_PATTERN.findall(text))
            if token.lower() not in JD_STOP_WORDS
        ]
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
    return TailoredSection(
        ref_id=experience.id, bullets=_fact_bullets(experience.facts)
    )


def project_section(project: Project) -> TailoredSection:
    """Convert confirmed project facts into grounded bullets."""
    return TailoredSection(ref_id=project.id, bullets=_fact_bullets(project.facts))


def mock_refactor_resume(master: MasterResume) -> TailoredResume:
    """Return a renderable resume using only confirmed master facts.

    Used by `refactor` in both modes: the no-JD path is a pass-through of
    already-confirmed facts, so there is nothing for an LLM to add.
    """
    return TailoredResume(
        summary_of_strategy="Mock refactor: preserve confirmed facts without rewriting.",
        experiences=[
            experience_section(experience) for experience in master.experiences
        ],
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


def mock_tailor_resume(
    master: MasterResume, jd: JDExtract
) -> tuple[TailoredResume, Report]:
    """Return grounded mock tailoring plus its validation report."""
    tailored = mock_refactor_resume(master)
    score, matched, missing = keyword_match(jd, master)
    tailored.summary_of_strategy = (
        "Mock tailor: preserve facts and report keyword overlap."
    )
    validate_grounding(master, tailored)
    return tailored, build_grounding_report(tailored, score, matched, missing)


def _tailor_user_prompt(jd: JDExtract) -> str:
    return (
        "Tailor the confirmed master resume in the system prompt to this "
        f"posting:\n\n{jd.model_dump_json(indent=2)}"
    )


def real_tailor_resume(
    master: MasterResume, jd: JDExtract, *, client: Any | None = None
) -> TailoredResume:
    """Tailor with Sonnet, then reject anything the validator will not accept.

    The master resume rides in the cached system block so repeated tailoring
    for one session reuses the prefix.
    """
    tailored = structured_call(
        TAILOR_MODEL,
        cacheable_system(TAILOR_SYSTEM, f"Confirmed master resume:\n{master.model_dump_json()}"),
        _tailor_user_prompt(jd),
        TailoredResume,
        client=client,
    )
    # Unvalidated output must never leave the pipeline.
    validate_grounding(master, tailored)
    return tailored


def real_tailor_result(
    master: MasterResume, jd: JDExtract, *, client: Any | None = None
) -> tuple[TailoredResume, Report]:
    """Return real tailored output plus its two-stage validation report."""
    tailored = real_tailor_resume(master, jd, client=client)
    score, matched, missing = keyword_match(jd, master)
    verdicts = judge_bullets(master, tailored, client=client)
    report = build_grounding_report(tailored, score, matched, missing)
    report.verdicts = verdicts
    report.grounding_ok = all(verdict.supported for verdict in verdicts)
    return tailored, report


def tailor(
    master: MasterResume, jd: JDExtract, *, client: Any | None = None
) -> TailoredResume:
    """Public tailor entrypoint; MOCK mode preserves confirmed facts."""
    if mock_enabled():
        tailored, _report = mock_tailor_resume(master, jd)
        return tailored
    return real_tailor_resume(master, jd, client=client)
