import pytest

from core.llm import LLMUnavailableError
from core.pipeline import (
    _entity_prefix,
    _fact_violations,
    _fix_name_casing,
    _parse_education_entry,
    _split_entries,
    _split_location,
    mock_polish_result,
    mock_polish_resume,
    mock_refactor_result,
    mock_refactor_resume,
    mock_tailor_resume,
    parse_jd,
    polish,
    refactor,
    structure_resume,
    tailor,
)
from core.schemas import JDExtract
from core.validation import validate_grounding


def test_entity_prefix_uses_initials_for_multiword_names():
    assert _entity_prefix("General Atomics", set()) == "GA"


def test_entity_prefix_prefers_an_existing_acronym():
    assert _entity_prefix("ACM @ UCR", set()) == "ACM"
    assert _entity_prefix("NASA California Space Grant Consortium", set()) == "NASA"


def test_entity_prefix_splits_a_camelcase_name_on_its_seam():
    assert _entity_prefix("TrailScout", set()) == "TS"
    assert _entity_prefix("ThreatSense", set()) == "TS"


def test_entity_prefix_keeps_a_name_whose_camel_tail_is_too_short():
    # "TermIt" -> Term + It; a two-letter tail isn't a word worth an initial
    assert _entity_prefix("TermIt", set()) == "TERMIT"
    assert _entity_prefix("Emend", set()) == "EMEND"


def test_fix_name_casing_capitalizes_an_all_lowercase_word():
    # a small-caps-styled PDF header extracts as lowercase text ("vila")
    # even though the resume visibly reads "Vila"
    assert _fix_name_casing("Sam A. vila") == "Sam A. Vila"
    assert _fix_name_casing("sam a. vila") == "Sam A. Vila"


def test_fix_name_casing_leaves_an_already_mixed_case_word_alone():
    # a word with any uppercase letter already looks intentional
    # ("McDonald") -- not distinguishable from a real casing, so untouched
    assert _fix_name_casing("Sam McDonald") == "Sam McDonald"


def test_fix_name_casing_leaves_a_lowercase_name_particle_alone():
    # a lone lowercase word mid-name is more likely a real particle than
    # the font artifact this function targets, which lowercases the whole
    # name uniformly, not just one word in the middle of it
    assert _fix_name_casing("Vincent van Gogh") == "Vincent van Gogh"
    assert _fix_name_casing("Wernher von Braun") == "Wernher von Braun"
    # a particle is never the first word of a name, so this is still the
    # real small-caps bug, not a name starting with "van"
    assert _fix_name_casing("van Gogh") == "Van Gogh"


def test_entity_prefix_adds_numeric_suffix_on_collision():
    used: set[str] = set()
    assert _entity_prefix("General Atomics", used) == "GA"
    assert _entity_prefix("General Atomics", used) == "GA2"


def test_split_entries_breaks_at_each_dated_header():
    lines = [
        "Software Engineer Intern Jun 2025 - Sep 2025",
        "General Atomics San Diego, CA",
        "• Wrote tests.",
        "Research Assistant Jan 2024 - Dec 2024",
        "NASA Los Angeles, CA",
        "• Analyzed telemetry.",
    ]

    assert _split_entries(lines, "experience") == [lines[:3], lines[3:]]


def test_split_entries_breaks_when_the_date_is_on_the_second_header_line():
    # "Technical Lead" carries no date of its own -- the line under it does
    lines = [
        "Software Engineer Intern Jun 2025 - Sep 2025",
        "General Atomics San Diego, CA",
        "• Wrote tests.",
        "Technical Lead",
        "ACM @ UCR Riverside, CA 2025",
        "• Led four students.",
    ]

    assert _split_entries(lines, "experience") == [lines[:3], lines[3:]]


def test_split_entries_breaks_at_each_bare_year_line_with_nothing_following():
    # three one-line certifications run together with no blank lines --
    # each carries its own bare year and none has a bulleted fact after it,
    # so the "following line has a date" rule alone can't segment them
    lines = [
        "AWS Certified Solutions Architect - Amazon, 2023",
        "Certified Kubernetes Administrator - CNCF, 2022",
        "Google Cloud Professional - Google, 2021",
    ]

    assert _split_entries(lines, "custom") == [[lines[0]], [lines[1]], [lines[2]]]


def test_split_entries_breaks_projects_at_a_tech_header():
    lines = [
        "Emend | Python, FastAPI",
        "• Built a resume service.",
        "TermIt | C++, CMake",
        "• Built a task manager.",
    ]

    assert _split_entries(lines, "project") == [lines[:2], lines[2:]]


def test_split_location_prefers_the_reading_that_keeps_the_org_name_whole():
    assert _split_location("University of California, Riverside Riverside, CA") == (
        "University of California, Riverside",
        "Riverside, CA",
    )
    assert _split_location("ACM @ UCR Riverside, CA") == ("ACM @ UCR", "Riverside, CA")
    assert _split_location("General Atomics San Diego, CA") == (
        "General Atomics",
        "San Diego, CA",
    )


def test_parse_education_entry_reads_a_two_line_header():
    education = _parse_education_entry(
        [
            "University of California, Riverside Riverside, CA",
            "Bachelor of Science in Computer Science Expected Jun 2027",
            "Coursework: Operating Systems, Edge Computing",
        ]
    )

    assert education.school == "University of California, Riverside"
    assert education.degree == "Bachelor of Science in Computer Science"
    assert education.location == "Riverside, CA"
    assert education.grad_date == "Expected Jun 2027"
    assert education.coursework == ["Operating Systems", "Edge Computing"]


def test_education_is_inferred_without_an_education_header():
    # no "Education" line anywhere -- a degree phrase plus a school is enough
    master = structure_resume(
        "Sam Sample\n"
        "sam@example.com\n"
        "\n"
        "Riverside State University Riverside, CA\n"
        "Bachelor of Science in Computer Science Expected May 2027\n"
        "\n"
        "Experience\n"
        "Software Engineer Intern Jun 2025 - Aug 2025\n"
        "Acme Corp, San Diego, CA\n"
        "• Built an internal tool for the support team.\n"
    )

    assert len(master.education) == 1
    assert master.education[0].school == "Riverside State University"
    assert master.education[0].degree == "Bachelor of Science in Computer Science"
    assert [e.company for e in master.experiences] == ["Acme Corp"]


def test_labeled_lines_become_skills_not_facts():
    master = structure_resume(
        "Sam Sample\n"
        "\n"
        "Experience\n"
        "Software Engineer Intern Jun 2025 - Aug 2025\n"
        "Acme Corp, San Diego, CA\n"
        "• Built an internal tool for the support team.\n"
        "\n"
        "Technical Skills\n"
        "Languages: Python, C++\n"
        "Tools/Testing: pytest, GoogleTest\n"
    )

    assert master.skills == {
        "Languages": ["Python", "C++"],
        "Tools/Testing": ["pytest", "GoogleTest"],
    }
    assert all("Languages" not in f.text for f in master.experiences[0].facts)


def test_fact_violations_flags_missing_terminal_punctuation():
    assert _fact_violations("Shipped a feature", "Acme", "Engineer")


def test_fact_violations_flags_fragment_continuation():
    assert _fact_violations("and validated the results.", "Acme", "Engineer")


def test_fact_violations_flags_bare_date_range():
    assert _fact_violations("Jun 2025 - Present", "Acme", "Engineer")


def test_fact_violations_flags_bare_city_state():
    assert _fact_violations("San Diego, CA", "Acme", "Engineer")


def test_fact_violations_flags_restated_company_or_title():
    assert _fact_violations("Acme.", "Acme", "Engineer")
    assert _fact_violations("Engineer.", "Acme", "Engineer")


def test_fact_violations_accepts_a_clean_sentence():
    assert _fact_violations("Shipped a feature used by 100+ customers.", "Acme", "Engineer") == []


def test_structure_resume_accepts_master_resume_json(sample_master):
    structured = structure_resume(sample_master.model_dump_json())

    assert structured == sample_master


def test_structure_resume_accepts_fenced_master_resume_json(sample_master):
    text = f"```json\n{sample_master.model_dump_json()}\n```"

    assert structure_resume(text) == sample_master


PASTED_RESUME = """\
Sam Sample
(555) 010-1010 | sam@example.com | linkedin.com/in/sam-sample

Software Engineer Intern, Acme Corp (Jun 2025 - Present)
• Built 25+ integration tests across 5 microservices.
• Automated a 12-step dev setup into one-click scripts.

Falcon Tracker
- Live-demoed an object detection app to 750+ attendees.
"""


def test_structure_resume_parses_pasted_text():
    master = structure_resume(PASTED_RESUME)

    assert master.name == "Sam Sample"
    assert master.email == "sam@example.com"
    assert master.links == ["linkedin.com/in/sam-sample"]
    assert len(master.experiences) == 2
    acme, falcon = master.experiences
    # a single combined header line can't be split further -- title and
    # company end up mirrored, but the date range is still pulled out
    assert acme.company == "Software Engineer Intern, Acme Corp"
    assert acme.start == "Jun 2025"
    assert acme.end == "Present"
    assert falcon.company == "Falcon Tracker"
    assert falcon.title == "Falcon Tracker"
    facts = master.fact_lookup()
    assert len(facts) == 3
    # bullets are stripped and the schema's id format holds end to end
    assert all(not fact.text.startswith(("•", "-")) for fact in facts.values())


def test_structure_resume_is_deterministic():
    assert structure_resume(PASTED_RESUME) == structure_resume(PASTED_RESUME)


def test_structure_resume_rejects_invalid_fenced_json():
    with pytest.raises(ValueError, match="invalid MasterResume JSON"):
        structure_resume("```json\n{not valid}\n```")


def test_structure_resume_ignores_incidental_braces():
    master = structure_resume("Sam Sample\n\nAcme\n• Shipped {feature flags} to prod.")

    assert master.experiences[0].facts[0].text == "Shipped {feature flags} to prod."


def test_structure_resume_splits_sections_without_blank_lines():
    # PDF copy-paste often collapses the blank lines between sections; a
    # known header should still start a new section on its own, and route to
    # the right list rather than becoming a fake "Education"/"Skills" entry.
    text = (
        "Sam Sample\n"
        "sam@example.com\n"
        "Education\n"
        "Riverside State University\n"
        "Expected 2027\n"
        "Experience\n"
        "Software Engineer Intern\n"
        "Acme Corp, Riverside, CA\n"
        "Built an internal tool for the support team.\n"
        "Skills\n"
        "Python, Docker\n"
    )

    master = structure_resume(text)

    assert len(master.education) == 1
    assert master.education[0].school == "Riverside State University"
    assert [e.company for e in master.experiences] == ["Acme Corp"]
    assert master.experiences[0].title == "Software Engineer Intern"
    assert master.experiences[0].facts[0].text == "Built an internal tool for the support team."


def test_structure_resume_captures_custom_sections():
    # regression: a header outside Education/Experience/Projects/Skills
    # used to either get silently dropped or bleed into the previous
    # section -- it must start its own named CustomSection instead,
    # including a bare, bulletless entry (a one-line certification)
    text = (
        "Sam Sample\n"
        "sam@example.com\n"
        "\n"
        "Experience\n"
        "Software Engineer Jun 2020 - Aug 2022\n"
        "Acme Corp, San Diego, CA\n"
        "Built an internal tool for the support team.\n"
        "\n"
        "Research Experience\n"
        "Research Assistant Jun 2019 - Aug 2020\n"
        "UCSD Bio Lab, La Jolla, CA\n"
        "Ran gel electrophoresis assays weekly.\n"
        "\n"
        "Certifications\n"
        "AWS Certified Solutions Architect\n"
        "Amazon 2023\n"
    )

    master = structure_resume(text)

    assert [e.company for e in master.experiences] == ["Acme Corp"]
    headings = [cs.heading for cs in master.custom_sections]
    assert headings == ["Research Experience", "Certifications"]

    research = master.custom_sections[0]
    assert research.entries[0].title == "Research Assistant"
    assert research.entries[0].facts[0].text == "Ran gel electrophoresis assays weekly."

    certifications = master.custom_sections[1]
    assert certifications.entries[0].title == "AWS Certified Solutions Architect"
    assert certifications.entries[0].facts == []


def test_structure_resume_rejects_oversized_text(monkeypatch):
    monkeypatch.setenv("MAX_TEXT_CHARS", "10")

    with pytest.raises(ValueError, match="exceeds 10 characters"):
        structure_resume("way more than ten characters")


def test_parse_jd_rejects_oversized_text(monkeypatch):
    monkeypatch.setenv("MAX_TEXT_CHARS", "10")

    with pytest.raises(ValueError, match="exceeds 10 characters"):
        parse_jd("way more than ten characters")


def test_structure_resume_requires_api_key_when_mock_disabled(monkeypatch, sample_master):
    monkeypatch.setenv("MOCK", "0")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(LLMUnavailableError, match="ANTHROPIC_API_KEY"):
        structure_resume(sample_master.model_dump_json())


def test_parse_jd_accepts_jd_extract_json():
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python"],
    )

    parsed = parse_jd(jd.model_dump_json())

    assert parsed == jd


def test_parse_jd_accepts_fenced_jd_extract_json():
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Docker"],
    )
    text = f"```json\n{jd.model_dump_json()}\n```"

    assert parse_jd(text) == jd


def test_parse_jd_rejects_invalid_fenced_json():
    with pytest.raises(ValueError, match="invalid JDExtract JSON"):
        parse_jd('```json\n{"keywords": ["Python"]\n```')


def test_parse_jd_derives_keywords_from_plain_text():
    parsed = parse_jd("Python backend role using Docker and Python.")

    assert parsed.responsibilities == ["Python backend role using Docker and Python."]
    # literal phrases pulled from the text itself, not a raw token dump --
    # "backend" and "role" are lowercase prose, not Capitalized proper nouns.
    # Order is priority (tier): "Python" (a language, tier 0) outranks
    # "Docker" (a platform, tier 1); see core/matching.py's _keyword_tier.
    assert parsed.keywords == ["Python", "Docker"]


def test_parse_jd_rejects_near_empty_text():
    # e.g. a JS-rendered posting page that failed to yield real content --
    # this must fail loudly, not silently score as a fake 0% match
    with pytest.raises(ValueError, match="too short to score"):
        parse_jd("enable JavaScript")


def test_parse_jd_rejects_a_bare_link_pasted_as_text():
    # pasted into the JD-text field instead of the dedicated link field --
    # extract_keywords finds a few literal path fragments in the URL, so
    # this doesn't hit the empty-keywords check either without its own guard
    with pytest.raises(ValueError, match="looks like a link"):
        parse_jd("https://careers.roblox.com/jobs/8080438?gh_jid=8080438")


def test_parse_jd_rejects_text_with_no_extractable_keywords():
    # long enough to pass the near-empty-text check, but flat prose with no
    # bullets, lead-in lists, or capitalized terms -- must fail loudly
    # instead of silently scoring a fake 0% match
    text = (
        "We want someone who can work well with others and communicate "
        "clearly with the team about what we are doing here for everyone "
        "involved in this effort every single day of the week."
    )
    with pytest.raises(ValueError, match="couldn't find any concrete requirements"):
        parse_jd(text)


def test_mock_refactor_preserves_fact_text_and_ids(sample_master):
    master = sample_master
    refactored = mock_refactor_resume(master)

    bullet = refactored.experiences[0].bullets[0]
    fact = master.experiences[0].facts[0]
    assert bullet.variants == [fact.text] * 3
    assert bullet.source_fact_ids == [fact.id]


def test_mock_refactor_passes_grounding_validation(sample_master):
    master = sample_master
    validate_grounding(master, mock_refactor_resume(master))


def test_refactor_entrypoint_returns_grounded_resume(sample_master):
    master = sample_master

    validate_grounding(master, refactor(master))


def test_refactor_entrypoint_preserves_all_fact_ids(sample_master):
    master = sample_master
    tailored = refactor(master)
    bullet_ids = {
        bullet.source_fact_ids[0]
        for section in [*tailored.experiences, *tailored.projects]
        for bullet in section.bullets
    }

    assert bullet_ids == master.all_fact_ids()


def test_mock_refactor_result_returns_grounded_report(sample_master):
    master = sample_master

    tailored, report = mock_refactor_result(master)

    validate_grounding(master, tailored)
    assert report.match_score == 0.0
    assert report.matched_keywords == []
    assert report.missing_keywords == []
    assert report.grounding_ok is True


def test_mock_polish_preserves_all_fact_ids(sample_master):
    master = sample_master
    polished = mock_polish_resume(master)

    bullet_ids = {
        bullet.source_fact_ids[0]
        for section in [*polished.experiences, *polished.projects]
        for bullet in section.bullets
    }
    assert bullet_ids == master.all_fact_ids()


def test_mock_polish_result_returns_grounded_report(sample_master):
    master = sample_master

    tailored, report = mock_polish_result(master)

    validate_grounding(master, tailored)
    assert report.match_score == 0.0
    assert report.grounding_ok is True


def test_polish_entrypoint_returns_grounded_resume(sample_master):
    master = sample_master

    validate_grounding(master, polish(master))


def test_mock_tailor_returns_grounded_resume_and_keyword_data(sample_master):
    master = sample_master
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python", "Kubernetes"],
    )

    tailored, report = mock_tailor_resume(master, jd)
    validate_grounding(master, tailored)
    assert report.match_score == 0.5
    assert report.matched_keywords == ["Python"]
    assert report.missing_keywords == ["Kubernetes"]
    assert report.grounding_ok is True


def test_tailor_entrypoint_returns_grounded_resume(sample_master):
    master = sample_master
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=[],
    )

    tailored = tailor(master, jd)

    validate_grounding(master, tailored)
