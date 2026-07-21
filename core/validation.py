"""Deterministic grounding checks for tailored resumes."""

from core.schemas import MasterResume, TailoredResume, TailoredSection


class GroundingError(ValueError):
    """Raised when generated content is not grounded in confirmed facts."""


def _validate_sections(
    sections: list[TailoredSection], fact_ids_by_ref: dict[str, set[str]]
) -> None:
    for section in sections:
        allowed_fact_ids = fact_ids_by_ref.get(section.ref_id)
        if allowed_fact_ids is None:
            raise GroundingError(f"unknown section ref_id: {section.ref_id}")
        for bullet in section.bullets:
            if not bullet.source_fact_ids:
                raise GroundingError(f"sourceless bullet: {bullet.text}")
            unknown_ids = set(bullet.source_fact_ids) - allowed_fact_ids
            if unknown_ids:
                raise GroundingError(f"unknown fact ids or outside-section ids: {sorted(unknown_ids)}")


def validate_grounding(master: MasterResume, tailored: TailoredResume) -> None:
    """Reject bullets that do not cite confirmed master-resume facts."""
    experience_facts = {e.id: {fact.id for fact in e.facts} for e in master.experiences}
    project_facts = {p.id: {fact.id for fact in p.facts} for p in master.projects}
    _validate_sections(tailored.experiences, experience_facts)
    _validate_sections(tailored.projects, project_facts)
