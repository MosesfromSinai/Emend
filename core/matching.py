"""Deterministic keyword matching for job descriptions."""

import re

from core.schemas import JDExtract, MasterResume

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def _master_text(master: MasterResume) -> str:
    facts = " ".join(fact.text for fact in master.fact_lookup().values())
    skills = " ".join(skill for group in master.skills.values() for skill in group)
    projects = " ".join(project.name for project in master.projects)
    return " ".join([facts, skills, projects])


def keyword_match(jd: JDExtract, master: MasterResume) -> tuple[float, list[str], list[str]]:
    """Return normalized keyword overlap without using an LLM."""
    resume_tokens = _tokens(_master_text(master))
    matched: list[str] = []
    missing: list[str] = []
    for keyword in jd.keywords:
        keyword_tokens = _tokens(keyword)
        if keyword_tokens and keyword_tokens <= resume_tokens:
            matched.append(keyword)
        else:
            missing.append(keyword)
    score = len(matched) / len(jd.keywords) if jd.keywords else 0.0
    return score, matched, missing
