import json
from pathlib import Path

from core.pipeline import (
    mock_refactor_result,
    mock_refactor_resume,
    mock_tailor_resume,
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
        company="", title="", hard_skills=[], soft_requirements=[], responsibilities=[], keywords=[]
    )

    tailored = tailor(master, jd)

    validate_grounding(master, tailored)
