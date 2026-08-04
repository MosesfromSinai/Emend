"""Two-stage grounding checks for tailored resumes.

Stage one is deterministic and authoritative: `validate_grounding` rejects
bullets that cite unknown facts, introduce unsupported numbers, or drift from
the wording of the facts they claim. Stage two is the LLM judge in
`judge_bullets`, which only runs in real mode and only after stage one passes.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from core.config import mock_enabled
from core.llm import FAST_MODEL, cacheable_system, structured_call_with_usage
from core.prompts import JUDGE_SYSTEM
from core.schemas import (
    BulletVerdict,
    MasterResume,
    Report,
    TailoredBullet,
    TailoredResume,
    TailoredSection,
)
from core.trace import record_call

NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?%?\+?(?![A-Za-z0-9])")
WORD_PATTERN = re.compile(r"[a-z0-9]+")
MIN_FACT_WORD_OVERLAP = 0.25
STOP_WORDS = {"a", "an", "and", "by", "for", "in", "of", "on", "the", "to", "with"}
JUDGE_MAX_WORKERS = 4


class GroundingError(ValueError):
    """Raised when generated content is not grounded in confirmed facts."""


def _numeric_tokens(text: str) -> set[str]:
    """Every integer, decimal, percentage, or +-suffixed count in `text`.

    Per the brief's "no derived numbers" rule: a bullet may only reuse a
    numeric token that appears literally in its cited facts. Percentages or
    deltas computed from two stated values (e.g. "80%" derived from "45" and
    "10", or "27" derived from "62" and "89") are not direct paraphrases —
    they're new claims a deterministic pass can catch, even though "the
    arithmetic is correct" is a judgment only the LLM judge could make.
    """
    return set(NUMBER_PATTERN.findall(text))


def _content_words(text: str) -> set[str]:
    return set(WORD_PATTERN.findall(text.lower())) - STOP_WORDS


def _has_fact_word_overlap(bullet_text: str, cited_text: str) -> bool:
    bullet_words = _content_words(bullet_text)
    cited_words = _content_words(cited_text)
    if not bullet_words or not cited_words:
        return True
    overlap = len(bullet_words & cited_words) / min(len(bullet_words), len(cited_words))
    return overlap >= MIN_FACT_WORD_OVERLAP


def _validate_sections(
    sections: list[TailoredSection], facts_by_ref: dict[str, dict[str, str]]
) -> None:
    seen_refs: set[str] = set()
    for section in sections:
        if section.ref_id in seen_refs:
            raise GroundingError(f"duplicate section ref_id: {section.ref_id}")
        seen_refs.add(section.ref_id)
        facts = facts_by_ref.get(section.ref_id)
        if facts is None:
            raise GroundingError(f"unknown section ref_id: {section.ref_id}")
        for bullet in section.bullets:
            if not bullet.source_fact_ids:
                raise GroundingError(f"sourceless bullet: {bullet.variants[0]}")
            unknown_ids = set(bullet.source_fact_ids) - set(facts)
            if unknown_ids:
                raise GroundingError(
                    f"unknown fact ids or outside-section ids: {sorted(unknown_ids)}"
                )
            cited_text = " ".join(facts[fact_id] for fact_id in bullet.source_fact_ids)
            # every variant is a real candidate for what ships -- each must
            # independently pass, not just one of the three
            for variant in bullet.variants:
                new_numbers = _numeric_tokens(variant) - _numeric_tokens(cited_text)
                if new_numbers:
                    raise GroundingError(f"unsupported numbers: {sorted(new_numbers)}")
                if not _has_fact_word_overlap(variant, cited_text):
                    raise GroundingError(f"low fact overlap: {variant}")


def _validate_skills(
    master_skills: dict[str, list[str]], tailored_skills: dict[str, list[str]]
) -> None:
    allowed = {skill.lower() for skills in master_skills.values() for skill in skills}
    for category, skills in tailored_skills.items():
        if category not in master_skills:
            raise GroundingError(f"unknown skill category: {category}")
        unsupported = {skill for skill in skills if skill.lower() not in allowed}
        if unsupported:
            raise GroundingError(f"unsupported skills: {sorted(unsupported)}")


def _experience_facts(master: MasterResume) -> dict[str, dict[str, str]]:
    return {e.id: {fact.id: fact.text for fact in e.facts} for e in master.experiences}


def _project_facts(master: MasterResume) -> dict[str, dict[str, str]]:
    return {p.id: {fact.id: fact.text for fact in p.facts} for p in master.projects}


def validate_grounding(master: MasterResume, tailored: TailoredResume) -> None:
    """Reject bullets that do not cite confirmed master-resume facts."""
    _validate_sections(tailored.experiences, _experience_facts(master))
    _validate_sections(tailored.projects, _project_facts(master))
    _validate_skills(master.skills, tailored.skills)


def build_grounding_report(
    tailored: TailoredResume, match_score: float, matched: list[str], missing: list[str]
) -> Report:
    """Build a deterministic report after grounding validation passes."""
    bullets = [
        bullet
        for section in [*tailored.experiences, *tailored.projects]
        for bullet in section.bullets
    ]
    verdicts = [
        BulletVerdict(
            bullet=bullet.variants[0],
            supported=True,
            reason="Passed deterministic grounding checks.",
            source_fact_ids=bullet.source_fact_ids,
        )
        for bullet in bullets
    ]
    return Report(
        match_score=match_score,
        matched_keywords=matched,
        missing_keywords=missing,
        grounding_ok=True,
        verdicts=verdicts,
    )


def _judge_prompt(variant: str, source_fact_ids: list[str], facts: dict[str, str]) -> str:
    cited = "\n".join(f"- {fact_id}: {facts[fact_id]}" for fact_id in source_fact_ids)
    return f"Confirmed source facts:\n{cited}\n\nRewritten bullet:\n{variant}"


def _judge_one(args: tuple[str, list[str], dict[str, str], Any]) -> BulletVerdict:
    variant, source_fact_ids, facts, client = args
    result = structured_call_with_usage(
        FAST_MODEL,
        cacheable_system(JUDGE_SYSTEM),
        _judge_prompt(variant, source_fact_ids, facts),
        BulletVerdict,
        client=client,
    )
    record_call(
        label="judge_bullet",
        model=FAST_MODEL,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cache_read_input_tokens=result.cache_read_input_tokens,
        cache_creation_input_tokens=result.cache_creation_input_tokens,
    )
    verdict = result.value
    # Trust the judgement, not the echo: keep our own variant text and fact
    # ids so a paraphrased echo cannot misattribute a verdict.
    return BulletVerdict(
        bullet=variant,
        supported=verdict.supported,
        reason=verdict.reason,
        source_fact_ids=source_fact_ids,
    )


def judge_bullets(
    master: MasterResume,
    tailored: TailoredResume,
    *,
    client: Any | None = None,
) -> list[BulletVerdict]:
    """Run the LLM judge over every tailored bullet (stage two of the guard).

    Assumes `validate_grounding` has already passed, so every cited id exists
    on its own section. Bullets are judged concurrently, bounded so a long
    resume can't fan out into an unbounded burst of API calls; `.map` returns
    results in submission order regardless of completion order, so verdicts
    still line up with the bullets they judge.
    """
    facts_by_ref = {**_experience_facts(master), **_project_facts(master)}
    jobs = [
        (bullet, facts_by_ref[section.ref_id], client)
        for section in [*tailored.experiences, *tailored.projects]
        for bullet in section.bullets
    ]
    if not jobs:
        return []
    with ThreadPoolExecutor(max_workers=min(JUDGE_MAX_WORKERS, len(jobs))) as pool:
        return list(pool.map(_judge_one, jobs))


def validate(
    master: MasterResume, tailored: TailoredResume
) -> tuple[bool, list[BulletVerdict]]:
    """Return API-friendly grounding status and verdicts.

    Stage one (deterministic) is authoritative and runs in every mode; a
    failure short-circuits before spending a judge call. Stage two (the LLM
    judge) runs only in real mode.
    """
    try:
        validate_grounding(master, tailored)
    except GroundingError as exc:
        return False, [BulletVerdict(bullet="", supported=False, reason=str(exc))]
    if mock_enabled():
        report = build_grounding_report(tailored, 0.0, [], [])
        return True, report.verdicts
    verdicts = judge_bullets(master, tailored)
    return all(verdict.supported for verdict in verdicts), verdicts
