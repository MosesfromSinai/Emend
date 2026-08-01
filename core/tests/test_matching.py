from core.matching import keyword_match
from core.schemas import JDExtract


def test_keyword_match_scores_overlap_deterministically(sample_master):
    jd = JDExtract(
        company="Analytical Jobs",
        title="Backend Engineer",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python", "Docker", "Kubernetes", "Bernoulli numbers"],
    )

    score, matched, missing = keyword_match(jd, sample_master)
    assert score == 0.75
    assert matched == ["Python", "Docker", "Bernoulli numbers"]
    assert missing == ["Kubernetes"]


def test_keyword_match_empty_keywords_scores_zero(sample_master):
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=[],
    )
    assert keyword_match(jd, sample_master) == (0.0, [], [])


def test_keyword_match_counts_project_tech(sample_master):
    # tech the candidate listed on a project is a real claim, not a company name
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Punch Cards"],
    )

    assert keyword_match(jd, sample_master) == (1.0, ["Punch Cards"], [])


def test_keyword_match_excludes_employer_names(sample_master):
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Babbage"],
    )

    score, matched, missing = keyword_match(jd, sample_master)
    assert (score, matched) == (0.0, [])
    assert missing == ["Babbage"]


def test_keyword_match_ignores_duplicate_and_blank_keywords(sample_master):
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python", "", "Python"],
    )

    assert keyword_match(jd, sample_master) == (1.0, ["Python"], [])
