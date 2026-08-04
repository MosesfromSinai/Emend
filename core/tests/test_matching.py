from core.matching import MAX_PHRASE_WORDS, extract_keywords, keyword_match
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


def test_extract_keywords_is_deterministic_across_calls():
    text = "We need a backend engineer with Python and PostgreSQL experience."
    assert extract_keywords(text) == extract_keywords(text)


def test_extract_keywords_ignores_generic_prose():
    keywords = extract_keywords("We need a great team player for this role.")
    assert keywords == []


def test_extract_keywords_pulls_literal_phrases_from_lead_in_lists():
    # "Experience with X and Y" is a structural signal, not a claim we
    # normalize or expand -- "k8s" stays "k8s", it never becomes "Kubernetes"
    keywords = extract_keywords("Experience with machine learning and k8s required.")
    assert keywords == ["machine learning", "k8s"]


def test_extract_keywords_catches_soft_skill_phrases_in_a_list():
    # the exact class of phrase a fixed tech-skills dictionary would miss
    text = (
        "Requirements: experience with cross-functional collaboration "
        "and stakeholder management."
    )
    keywords = extract_keywords(text)
    assert "cross-functional collaboration" in keywords
    assert "stakeholder management" in keywords


def test_extract_keywords_reads_one_bullet_per_line():
    text = "Requirements:\nPython\nDocker\nStrong communication skills\n"
    assert extract_keywords(text) == ["Python", "Docker", "Strong communication skills"]


def test_extract_keywords_ignores_capitalized_sentence_starters():
    # "Experience" here is only capitalized because it starts the sentence,
    # not because it's a real proper noun -- must not show up as a keyword
    keywords = extract_keywords("Experience with Python is required.")
    assert "Experience" not in keywords
    assert "Python" in keywords


def test_extract_keywords_does_not_shred_a_whole_flattened_page():
    # a URL-fetched posting has no real line breaks (core/jd_text.py joins
    # every block into one line) -- a long line with no terminal punctuation
    # must not be treated as one giant bullet and split on every and/or/comma
    text = "Build accessible components and contribute to design systems " * 20
    keywords = extract_keywords(text.strip())
    assert all(len(k.split()) <= MAX_PHRASE_WORDS for k in keywords)
