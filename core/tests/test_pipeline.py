import json
from pathlib import Path

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
from core.schemas import JDExtract, MasterResume
from core.validation import validate_grounding

FIXTURES = Path(__file__).resolve().parents[2] / "latex/tests/fixtures"


def _master() -> MasterResume:
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    return MasterResume(**data)


def test_structure_resume_accepts_master_resume_json():
    master = _master()

    structured = structure_resume(master.model_dump_json())

    assert structured == master


def test_structure_resume_accepts_fenced_master_resume_json():
    master = _master()
    text = f"```json\n{master.model_dump_json()}\n```"

    assert structure_resume(text) == master


def test_structure_resume_requires_api_key_when_mock_disabled(monkeypatch):
    monkeypatch.setenv("MOCK", "0")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(LLMUnavailableError, match="ANTHROPIC_API_KEY"):
        structure_resume(_master().model_dump_json())


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


def test_mock_refactor_preserves_fact_text_and_ids():
    master = _master()
    refactored = mock_refactor_resume(master)

    bullet = refactored.experiences[0].bullets[0]
    fact = master.experiences[0].facts[0]
    assert bullet.text == fact.text
    assert bullet.source_fact_ids == [fact.id]


def test_mock_refactor_passes_grounding_validation():
    master = _master()
    validate_grounding(master, mock_refactor_resume(master))


def test_refactor_entrypoint_returns_grounded_resume():
    master = _master()

    validate_grounding(master, refactor(master))


def test_refactor_entrypoint_preserves_all_fact_ids():
    master = _master()
    tailored = refactor(master)
    bullet_ids = {
        bullet.source_fact_ids[0]
        for section in [*tailored.experiences, *tailored.projects]
        for bullet in section.bullets
    }

    assert bullet_ids == master.all_fact_ids()


def test_mock_refactor_result_returns_grounded_report():
    master = _master()

    tailored, report = mock_refactor_result(master)

    validate_grounding(master, tailored)
    assert report.match_score == 0.0
    assert report.matched_keywords == []
    assert report.missing_keywords == []
    assert report.grounding_ok is True


def test_mock_tailor_returns_grounded_resume_and_keyword_data():
    master = _master()
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


def test_tailor_entrypoint_returns_grounded_resume():
    master = _master()
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
