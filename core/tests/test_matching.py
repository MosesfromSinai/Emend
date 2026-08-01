import json
from pathlib import Path

from core.matching import keyword_match
from core.schemas import JDExtract, MasterResume

FIXTURES = Path(__file__).resolve().parents[2] / "latex/tests/fixtures"


def _master() -> MasterResume:
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    return MasterResume(**data)


def test_keyword_match_scores_overlap_deterministically():
    jd = JDExtract(
        company="Analytical Jobs",
        title="Backend Engineer",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python", "Docker", "Kubernetes", "Bernoulli numbers"],
    )

    score, matched, missing = keyword_match(jd, _master())
    assert score == 0.75
    assert matched == ["Python", "Docker", "Bernoulli numbers"]
    assert missing == ["Kubernetes"]


def test_keyword_match_empty_keywords_scores_zero():
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=[],
    )
    assert keyword_match(jd, _master()) == (0.0, [], [])


def test_keyword_match_counts_project_tech():
    # tech the candidate listed on a project is a real claim, not a company name
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Punch Cards"],
    )

    assert keyword_match(jd, _master()) == (1.0, ["Punch Cards"], [])


def test_keyword_match_excludes_employer_names():
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Analytical Society"],
    )

    score, matched, missing = keyword_match(jd, _master())
    assert (score, matched) == (0.0, [])
    assert missing == ["Analytical Society"]


def test_keyword_match_ignores_duplicate_and_blank_keywords():
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python", "", "Python"],
    )

    assert keyword_match(jd, _master()) == (1.0, ["Python"], [])
