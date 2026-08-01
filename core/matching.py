"""Deterministic keyword matching for job descriptions."""

import re

from core.schemas import JDExtract, MasterResume

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def _master_text(master: MasterResume) -> str:
    """Searchable corpus: facts, skills, project names, and project tech.

    Company, title, and coursework are deliberately excluded — a JD keyword
    matching only an employer name is not a skill the candidate claimed.
    """
    facts = " ".join(fact.text for fact in master.fact_lookup().values())
    skills = " ".join(skill for group in master.skills.values() for skill in group)
    projects = " ".join(
        " ".join([project.name, *project.tech]) for project in master.projects
    )
    return " ".join([facts, skills, projects])


def _unique_keywords(keywords: list[str]) -> list[str]:
    return list(dict.fromkeys(keyword for keyword in keywords if keyword.strip()))


def keyword_match(
    jd: JDExtract, master: MasterResume
) -> tuple[float, list[str], list[str]]:
    """Return normalized keyword overlap without using an LLM."""
    resume_tokens = _tokens(_master_text(master))
    matched: list[str] = []
    missing: list[str] = []
    keywords = _unique_keywords(jd.keywords)
    for keyword in keywords:
        keyword_tokens = _tokens(keyword)
        if keyword_tokens and keyword_tokens <= resume_tokens:
            matched.append(keyword)
        else:
            missing.append(keyword)
    score = len(matched) / len(keywords) if keywords else 0.0
    return score, matched, missing
