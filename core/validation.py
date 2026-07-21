"""Deterministic grounding checks for tailored resumes."""

import re

from core.schemas import MasterResume, TailoredResume, TailoredSection

NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?%?\+?\b")


class GroundingError(ValueError):
    """Raised when generated content is not grounded in confirmed facts."""


def _validate_sections(
    sections: list[TailoredSection], facts_by_ref: dict[str, dict[str, str]]
) -> None:
    for section in sections:
        facts = facts_by_ref.get(section.ref_id)
        if facts is None:
            raise GroundingError(f"unknown section ref_id: {section.ref_id}")
        for bullet in section.bullets:
            if not bullet.source_fact_ids:
                raise GroundingError(f"sourceless bullet: {bullet.text}")
            unknown_ids = set(bullet.source_fact_ids) - set(facts)
            if unknown_ids:
                raise GroundingError(f"unknown fact ids or outside-section ids: {sorted(unknown_ids)}")
            cited_text = " ".join(facts[fact_id] for fact_id in bullet.source_fact_ids)
            new_numbers = set(NUMBER_PATTERN.findall(bullet.text)) - set(
                NUMBER_PATTERN.findall(cited_text)
            )
            if new_numbers:
                raise GroundingError(f"unsupported numbers: {sorted(new_numbers)}")


def validate_grounding(master: MasterResume, tailored: TailoredResume) -> None:
    """Reject bullets that do not cite confirmed master-resume facts."""
    experience_facts = {e.id: {fact.id: fact.text for fact in e.facts} for e in master.experiences}
    project_facts = {p.id: {fact.id: fact.text for fact in p.facts} for p in master.projects}
    _validate_sections(tailored.experiences, experience_facts)
    _validate_sections(tailored.projects, project_facts)
