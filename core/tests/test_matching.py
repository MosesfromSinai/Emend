from core.matching import (
    MAX_PHRASE_WORDS,
    drop_known_names,
    extract_keywords,
    keyword_match,
)
from core.schemas import CustomEntry, CustomSection, Experience, Fact, JDExtract, MasterResume


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


def test_keyword_match_counts_custom_section_facts():
    # a custom section's facts count toward matching automatically, via
    # fact_lookup() -- no matching.py changes needed to support them
    master = MasterResume(
        name="Jamie Doe",
        email="jamie@example.com",
        phone="555-010-1010",
        links=[],
        education=[],
        experiences=[],
        projects=[],
        skills={},
        custom_sections=[
            CustomSection(
                key="RESEARCH",
                heading="Research Experience",
                entries=[
                    CustomEntry(
                        id="RES",
                        title="Research Assistant",
                        subtitle="UCSD Bio Lab",
                        facts=[Fact(id="RES-01", text="Ran gel electrophoresis assays weekly")],
                    )
                ],
            )
        ],
    )
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["gel electrophoresis"],
    )

    assert keyword_match(jd, master) == (1.0, ["gel electrophoresis"], [])


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


def test_extract_keywords_denies_a_denylisted_acronym_even_spelled_out():
    # "gnc" is denylisted as a bare acronym (too org-specific to generalize)
    # -- spelling it out with its own parenthetical shouldn't smuggle the
    # same excluded term back in under its long form
    assert extract_keywords("Experience with Guidance Navigation Control (GNC) required.") == []
    assert extract_keywords("Familiarity with Standard Template Library (STL) is a plus.") == []


def test_extract_keywords_collapses_an_accidentally_repeated_word():
    # a copy-pasted posting can genuinely repeat a word back to back (a
    # hidden SEO/accessibility text node duplicating the visible text is a
    # common real-world cause) -- "Salesforce Salesforce" is never itself a
    # distinct keyword, so it collapses to one occurrence
    keywords = extract_keywords(
        "Join Salesforce Salesforce and define the future of cloud computing."
    )
    assert "Salesforce Salesforce" not in keywords
    assert keywords == ["Salesforce", "cloud computing"]


def test_extract_keywords_then_drop_known_names_removes_the_posting_own_company():
    # "Salesforce" is a real, independently curated CRM platform -- a
    # legitimate skill on someone else's posting -- but on a posting FROM
    # Salesforce, every mention of it is the employer's own name, not a
    # requirement. extract_keywords doesn't know who posted the JD, so
    # dropping it is drop_known_names's job once parse_jd knows the
    # company; this pins that the two compose correctly.
    keywords = extract_keywords(
        "Join Salesforce Salesforce and define the future of cloud computing."
    )
    assert drop_known_names(keywords, "Salesforce", "Software Engineer") == ["cloud computing"]


def test_extract_keywords_drops_soft_skill_phrases_in_a_list():
    # only a real language/framework/library/platform/tool counts now --
    # a structurally perfect list item is still dropped if it isn't one,
    # while a genuine technology in the very same list survives
    text = (
        "Requirements: experience with cross-functional collaboration, "
        "stakeholder management, and Kubernetes."
    )
    keywords = extract_keywords(text)
    assert "cross-functional collaboration" not in keywords
    assert "stakeholder management" not in keywords
    assert "Kubernetes" in keywords


def test_extract_keywords_keeps_short_terms_that_are_letter_substrings():
    # "Java" is not a redundant wrapper of "JavaScript" just because the
    # letters line up -- same for "C" inside "C++" and "Go" inside "MongoDB"
    text = "Requirements: Java, JavaScript, Python, C, C++, Go, MongoDB."
    keywords = extract_keywords(text)
    for term in ("Java", "JavaScript", "C", "C++", "Go", "MongoDB"):
        assert term in keywords


def test_extract_keywords_reads_one_bullet_per_line():
    # "Strong communication skills" is exactly the generic soft-skill
    # boilerplate _PROCESS_NOISE exists to drop -- every word in it is
    # noise ("strong"/"skills" are stopwords, "communication" is process
    # noise), so only the two real bulleted technologies survive.
    text = "Requirements:\nPython\nDocker\nStrong communication skills\n"
    assert extract_keywords(text) == ["Python", "Docker"]


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


def test_extract_keywords_still_catches_capitalized_terms_after_you_have_will():
    # "You Have:"/"You Will:" is deliberately NOT a recognized list lead-in
    # (see test_extract_keywords_ignores_prose_after_you_will_and_you_are
    # below) -- but real product/tool names right after it still surface via
    # the proper-noun heuristic on its own, lead-in or not.
    text = (
        "You Have: 3+ years with Kubernetes and Terraform. "
        "You Will: Build reliable, scalable infrastructure."
    )
    keywords = extract_keywords(text)
    assert "Kubernetes" in keywords
    assert "Terraform" in keywords


def test_extract_keywords_ignores_prose_after_you_will_and_you_are():
    # regression: "You Will:"/"You Are:" on most postings introduces
    # full-sentence responsibilities/qualifications, not a literal list --
    # treating it as a list lead-in shredded ordinary prose commas into fake
    # keywords like "supportive engineers" and "Pursuing" (from a real
    # Roblox posting: "You Will: Join a community of curious, supportive
    # engineers, actively engaging..." and "You Are: Pursuing or in
    # possession of...").
    text = (
        "You Will: Join a community of curious, supportive engineers, "
        "actively engaging in architectural discussions and system design. "
        "You Are: Pursuing or in possession of an undergraduate degree."
    )
    keywords = extract_keywords(text)
    assert "supportive engineers" not in keywords
    assert "Pursuing" not in keywords


def test_extract_keywords_reads_comma_like_lists():
    # "technologies, like X and Y" is a reliable list cue precisely because
    # it requires the preceding comma -- bare "like" elsewhere (e.g. "we'd
    # like to") is not a list lead-in and must not be treated as one.
    text = (
        "Investigate cutting-edge technologies, like machine learning "
        "frameworks and large language models (LLMs), to solve problems. "
        "We'd like to hear from you about your career goals."
    )
    # trimmed to the recognized technology, not kept as a whole with its
    # generic tail ("frameworks") still attached -- see _known_technical_span
    keywords = extract_keywords(text)
    assert "machine learning" in keywords
    assert "large language models" in keywords or "LLMs" in keywords
    assert not any("like to hear" in k.lower() for k in keywords)


def test_extract_keywords_keeps_symbol_suffixed_languages_whole():
    # regression: a trailing \b after a symbol class member (# or +) can
    # never match when immediately followed by another non-word char (a
    # comma) -- that silently truncated "C#"/"C++" down to a bare "C".
    text = "Proficient in C#, Lua, Java, Go, Node.js, Ruby, Python, C++, and Swift."
    keywords = extract_keywords(text)
    assert "C#" in keywords
    assert "C++" in keywords
    assert "C" not in keywords


def test_extract_keywords_does_not_fracture_a_four_word_tech_name():
    # regression: a 3-word cap on the proper-noun run split a real 4-word
    # technology name into a truncated fragment + a stray leftover word
    # instead of one coherent phrase.
    text = "Requirements: production experience with Amazon Web Services required."
    keywords = extract_keywords(text)
    assert "Amazon Web Services" in keywords
    assert "Services" not in keywords
    assert "Amazon Web" not in keywords


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


def test_drop_known_names_drops_a_parenthesized_team_name():
    # regression: "Software Engineer, C++ Simulations (Starlink)" only
    # split on the comma, so "Starlink" (parenthesized onto the title to
    # name the team, not a skill) never became its own blocked segment
    keywords = drop_known_names(
        ["STARLINK", "C++", "Python"],
        "SpaceX",
        "Software Engineer, C++ Simulations (Starlink)",
    )
    assert keywords == ["C++", "Python"]


def test_extract_keywords_ignores_city_state_addresses():
    text = "Software Engineer San Mateo, CA, United States. Experience with Kubernetes required."
    keywords = extract_keywords(text)
    assert "Mateo" not in keywords
    assert "CA" not in keywords
    assert "Kubernetes" in keywords


def test_extract_keywords_reads_such_as_lists_in_prose():
    # a "such as" clause mid-sentence is as reliable a list signal as an
    # explicit "Requirements:" heading -- real technologies named in one
    # survive, generic quality adjectives named alongside them do not
    text = (
        "An understanding of backend frameworks such as "
        "Django, accessibility, and Flask."
    )
    keywords = extract_keywords(text)
    assert "Django" in keywords
    assert "Flask" in keywords
    assert "accessibility" not in keywords


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


def test_extract_keywords_ignores_compensation_and_legal_boilerplate():
    # regression: a real SpaceX posting's compensation/benefits and
    # ITAR/EEO legal tail produced keywords like "Pay Range", "Level",
    # "Employee Stock Purchase Plan", "Seattle", "Refugee", "U.S.C", and
    # "Asylee" -- none of it is ever a real technical requirement, and it
    # comes after the real qualifications on every posting that has it, so
    # the whole tail must be cut before any heuristic ever sees it.
    text = (
        "Requirements: Experience with Python and Kubernetes.\n"
        "ADDITIONAL REQUIREMENTS:\n"
        "Willing to work extended hours and weekends when needed.\n"
        "COMPENSATION AND BENEFITS:\n"
        "Pay Range:\n"
        "Level 1: $125,000.00 - $165,000.00\n"
        "You may purchase stock through an Employee Stock Purchase Plan. "
        "Company shuttles are offered from select Seattle locations.\n"
        "ITAR REQUIREMENTS:\n"
        "Applicant must be a U.S. citizen, or a Refugee under 8 U.S.C. "
        "Section 1157, or an Asylee under 8 U.S.C. Section 1158.\n"
        "SpaceX is an Equal Opportunity Employer."
    )
    keywords = extract_keywords(text)
    assert "Python" in keywords
    assert "Kubernetes" in keywords
    for banned in (
        "ADDITIONAL REQUIREMENTS", "Pay Range", "Level",
        "Employee Stock Purchase Plan", "Seattle", "Refugee", "U.S.C",
        "Asylee",
    ):
        assert banned not in keywords
