"""Deterministic grounding checks for tailored resumes."""

from core.schemas import MasterResume, TailoredResume, TailoredSection


class GroundingError(ValueError):
    """Raised when generated content is not grounded in confirmed facts."""


def _validate_sections(
    sections: list[TailoredSection], known_ref_ids: set[str], known_fact_ids: set[str]
) -> None:
    for section in sections:
        if section.ref_id not in known_ref_ids:
            raise GroundingError(f"unknown section ref_id: {section.ref_id}")
        for bullet in section.bullets:
            if not bullet.source_fact_ids:
                raise GroundingError(f"sourceless bullet: {bullet.text}")
            unknown_ids = set(bullet.source_fact_ids) - known_fact_ids
            if unknown_ids:
                raise GroundingError(f"unknown fact ids: {sorted(unknown_ids)}")


def validate_grounding(master: MasterResume, tailored: TailoredResume) -> None:
    """Reject bullets that do not cite confirmed master-resume facts."""
    known_fact_ids = master.all_fact_ids()
    experience_ids = {experience.id for experience in master.experiences}
    project_ids = {project.id for project in master.projects}
    _validate_sections(tailored.experiences, experience_ids, known_fact_ids)
    _validate_sections(tailored.projects, project_ids, known_fact_ids)
