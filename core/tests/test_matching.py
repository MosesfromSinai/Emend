from core.matching import (
    MAX_PHRASE_WORDS,
    drop_known_names,
    extract_keywords,
    keyword_match,
)
from core.schemas import Experience, Fact, JDExtract, MasterResume


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


def test_keyword_match_does_not_match_words_scattered_across_facts():
    # "team", "leadership", and "experience" each appear in the resume, but
    # in three unrelated facts that never jointly claim team-leadership
    # experience -- a whole-resume bag-of-words test would wrongly mark
    # "Team Leadership Experience" as matched. Each word must land inside a
    # single fact/skill/project unit to count.
    master = MasterResume(
        name="Jamie Doe",
        email="jamie@example.com",
        phone="555-010-1010",
        links=[],
        education=[],
        experiences=[
            Experience(
                id="ACME",
                company="Acme Corp",
                title="Engineer",
                location="Remote",
                start="Jan 2020",
                end="Jan 2022",
                facts=[
                    Fact(id="ACME-01", text="Worked on a team of 5 engineers"),
                    Fact(
                        id="ACME-02",
                        text="Gained experience with CI/CD pipelines",
                    ),
                    Fact(id="ACME-03", text="Club leadership role"),
                ],
            )
        ],
        projects=[],
        skills={},
    )
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Team Leadership Experience"],
    )

    score, matched, missing = keyword_match(jd, master)
    assert (score, matched) == (0.0, [])
    assert missing == ["Team Leadership Experience"]


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


def test_extract_keywords_keeps_short_terms_that_are_letter_substrings():
    # "Java" is not a redundant wrapper of "JavaScript" just because the
    # letters line up -- same for "C" inside "C++" and "Go" inside "MongoDB"
    text = "Requirements: Java, JavaScript, Python, C, C++, Go, MongoDB."
    keywords = extract_keywords(text)
    for term in ("Java", "JavaScript", "C", "C++", "Go", "MongoDB"):
        assert term in keywords


def test_extract_keywords_reads_one_bullet_per_line():
    text = "Requirements:\nPython\nDocker\nStrong communication skills\n"
    assert extract_keywords(text) == ["Python", "Docker", "Strong communication skills"]


def test_extract_keywords_ignores_capitalized_sentence_starters():
    # "Experience" here is only capitalized because it starts the sentence,
    # not because it's a real proper noun -- must not show up as a keyword
    keywords = extract_keywords("Experience with Python is required.")
    assert "Experience" not in keywords
    assert "Python" in keywords


def test_extract_keywords_ignores_calendar_words():
    # a flattened posting mentioning office days must not surface the day
    # names themselves as keywords
    text = "Our office is open Monday through Friday, with flexible hours on Tuesday and Wednesday."
    keywords = extract_keywords(text)
    for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
        assert day not in keywords


def test_extract_keywords_ignores_pronoun_led_fragments():
    # "You Have"/"You Will" are sentence fragments, not proper nouns, even
    # though both words happen to be Capitalized in the flattened text
    text = "You Have strong communication skills. You Will contribute to design systems."
    keywords = extract_keywords(text)
    assert "You Have" not in keywords
    assert "You Will" not in keywords


def test_extract_keywords_pulls_from_you_have_and_you_will_lead_ins():
    # common ATS bold-lead-in pattern in place of real "Requirements"/
    # "Responsibilities" headings -- must read as a real list, not get
    # discarded as a pronoun-led sentence fragment
    text = (
        "You Have: 3+ years with Kubernetes and Terraform. "
        "You Will: Build reliable, scalable infrastructure."
    )
    keywords = extract_keywords(text)
    assert "Kubernetes" in keywords
    assert "Terraform" in keywords


def test_extract_keywords_does_not_truncate_mid_word_at_the_window_cutoff():
    # a lead-in list with no sentence-ending punctuation for well over 120
    # chars must not leave a chopped-off partial word as a "keyword"
    text = "Requirements: " + (
        "several years of experience in one or more widely used programming languages"
    )
    keywords = extract_keywords(text)
    assert not any(k.endswith("langu") or k == "langu" for k in keywords)


def test_extract_keywords_drops_the_employers_own_name_and_title():
    keywords = drop_known_names(
        extract_keywords(
            "Software Engineer at Roblox. At Roblox, we build immersive experiences with Lua."
        ),
        "Roblox",
        "Software Engineer",
    )
    assert "Roblox" not in keywords
    assert "Software Engineer" not in keywords
    assert "Lua" in keywords


def test_drop_known_names_keeps_a_skill_that_is_merely_a_substring_of_the_title():
    # "Java" is a real, independently-listed requirement here, not just an
    # echo of the title -- it must survive even though "java" is a
    # substring of "java developer".
    keywords = drop_known_names(
        extract_keywords(
            "Java Developer at Acme. Requirements: Java, Spring Boot, SQL."
        ),
        "Acme",
        "Java Developer",
    )
    assert "Java" in keywords
    assert "Spring Boot" in keywords


def test_drop_known_names_drops_a_comma_separated_title_segment():
    # "Software Engineer, User Frameworks" is still just the title split
    # across a comma -- both halves are the title, not a claimed skill
    keywords = drop_known_names(
        ["Software Engineer", "User Frameworks", "Lua"],
        "Roblox",
        "Software Engineer, User Frameworks",
    )
    assert keywords == ["Lua"]


def test_extract_keywords_ignores_city_state_addresses():
    text = "Software Engineer San Mateo, CA, United States. Experience with Kubernetes required."
    keywords = extract_keywords(text)
    assert "Mateo" not in keywords
    assert "CA" not in keywords
    assert "Kubernetes" in keywords


def test_extract_keywords_reads_such_as_lists_in_prose():
    # a "such as" clause mid-sentence is as reliable a list signal as an
    # explicit "Requirements:" heading, and often the only place lowercase
    # quality-adjacent terms like "accessibility" ever show up literally
    text = (
        "An understanding of software quality fundamentals such as "
        "performance, accessibility, and maintainability."
    )
    keywords = extract_keywords(text)
    assert "performance" in keywords
    assert "accessibility" in keywords
    assert "maintainability" in keywords


def test_extract_keywords_ignores_bullet_leading_verbs():
    # "- Analyze campaign..." puts the bullet marker between the newline and
    # the capitalized verb -- that verb is a sentence-starter, not a term
    text = (
        "Responsibilities:\n"
        "- Analyze campaign performance data.\n"
        "- Conduct statistical analysis using SQL.\n"
        "- Present insights to leadership."
    )
    keywords = extract_keywords(text)
    assert "Analyze" not in keywords
    assert "Conduct" not in keywords
    assert "Present" not in keywords
    assert "SQL" in keywords


def test_extract_keywords_ignores_word_right_after_a_colon():
    # "About Acme: Founded in 2005..." -- "Founded" only looks like a term
    # because it follows a colon, not because it's a real proper noun
    text = "About Acme: Founded in 2005, we serve customers with Python and AWS."
    keywords = extract_keywords(text)
    assert "Founded" not in keywords
    assert "Python" in keywords
    assert "AWS" in keywords


def test_extract_keywords_does_not_shred_a_whole_flattened_page():
    # a URL-fetched posting has no real line breaks (core/jd_text.py joins
    # every block into one line) -- a long line with no terminal punctuation
    # must not be treated as one giant bullet and split on every and/or/comma
    text = "Build accessible components and contribute to design systems " * 20
    keywords = extract_keywords(text.strip())
    assert all(len(k.split()) <= MAX_PHRASE_WORDS for k in keywords)
