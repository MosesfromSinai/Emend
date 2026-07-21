"""Deterministic mock pipeline helpers."""

from core.schemas import Experience, Project, TailoredBullet, TailoredSection


def _fact_bullets(facts) -> list[TailoredBullet]:
    return [TailoredBullet(text=fact.text, source_fact_ids=[fact.id]) for fact in facts]


def experience_section(experience: Experience) -> TailoredSection:
    """Convert confirmed experience facts into grounded bullets."""
    return TailoredSection(ref_id=experience.id, bullets=_fact_bullets(experience.facts))


def project_section(project: Project) -> TailoredSection:
    """Convert confirmed project facts into grounded bullets."""
    return TailoredSection(ref_id=project.id, bullets=_fact_bullets(project.facts))
