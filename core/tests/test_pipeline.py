import pytest

from core.llm import LLMUnavailableError
from core.pipeline import (
    mock_refactor_result,
    mock_refactor_resume,
    mock_tailor_resume,
    parse_jd,
    refactor,
    structure_resume,
    tailor,
)
from core.schemas import JDExtract
from core.validation import validate_grounding


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
• Built 25+ integration tests across 5 microservices
• Automated a 12-step dev setup into one-click scripts

Falcon Tracker
- Live-demoed an object detection app to 750+ attendees
"""


def test_structure_resume_parses_pasted_text():
    master = structure_resume(PASTED_RESUME)

    assert master.name == "Sam Sample"
    assert master.email == "sam@example.com"
    assert master.links == ["linkedin.com/in/sam-sample"]
    assert [e.company for e in master.experiences] == [
        "Software Engineer Intern, Acme Corp (Jun 2025 - Present)",
        "Falcon Tracker",
    ]
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
    master = structure_resume("Sam Sample\n\nAcme\n• Shipped {feature flags} to prod")

    assert master.experiences[0].facts[0].text == "Shipped {feature flags} to prod"


def test_structure_resume_splits_sections_without_blank_lines():
    # PDF copy-paste often collapses the blank lines between sections; a
    # known header should still start a new section on its own.
    text = (
        "Sam Sample\n"
        "sam@example.com\n"
        "Education\n"
        "Riverside State University\n"
        "Experience\n"
        "Software Engineer Intern, Acme Corp\n"
        "Skills\n"
        "Python, Docker\n"
    )

    master = structure_resume(text)

    assert [e.company for e in master.experiences] == [
        "Education",
        "Experience",
        "Skills",
    ]
    assert master.experiences[1].facts[0].text == "Software Engineer Intern, Acme Corp"


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
    assert parsed.keywords == ["Python", "backend", "role", "Docker"]


def test_mock_refactor_preserves_fact_text_and_ids(sample_master):
    master = sample_master
    refactored = mock_refactor_resume(master)

    bullet = refactored.experiences[0].bullets[0]
    fact = master.experiences[0].facts[0]
    assert bullet.text == fact.text
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
