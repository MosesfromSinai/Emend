import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.schemas import Fact, MasterResume, TailoredBullet, TailoredResume
from core.validation import (
    GroundingError,
    build_grounding_report,
    validate,
    validate_grounding,
)

FIXTURES = Path(__file__).resolve().parents[2] / "latex/tests/fixtures"


def _load_fixture(filename: str, schema):
    data = json.loads((FIXTURES / filename).read_text())
    return schema(**data)


def test_validate_grounding_accepts_known_fact_ids():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)

    validate_grounding(master, tailored)


def test_validate_grounding_rejects_sourceless_bullet():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[0].source_fact_ids = []

    with pytest.raises(GroundingError, match="sourceless bullet"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unknown_fact_id():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[0].source_fact_ids = ["FAKE-99"]

    with pytest.raises(GroundingError, match="unknown fact ids"):
        validate_grounding(master, tailored)


def test_tailored_bullet_rejects_duplicate_source_fact_ids():
    with pytest.raises(ValidationError, match="source_fact_ids must be unique"):
        TailoredBullet(text="Repeated receipt", source_fact_ids=["BAB-01", "BAB-01"])


def test_validate_grounding_rejects_project_fact_on_experience():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[0].source_fact_ids = ["BERN-01"]

    with pytest.raises(GroundingError, match="outside-section ids"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_duplicate_tailored_ref_id():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences.append(tailored.experiences[0].model_copy(deep=True))

    with pytest.raises(GroundingError, match="duplicate section ref_id"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unsupported_numbers():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[1].text = "Boosted processing throughput 95%"

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unsupported_plus_numbers():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[
        0
    ].text = "Authored the first algorithm for 20+ users"

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_accepts_supported_plus_numbers():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[0].text = "Documented the module for 100+ users"
    tailored.experiences[0].bullets[0].source_fact_ids = ["BAB-03"]

    validate_grounding(master, tailored)


def test_validate_grounding_rejects_low_fact_overlap():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[
        0
    ].text = "Led Kubernetes migrations for payment systems"

    with pytest.raises(GroundingError, match="low fact overlap"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unsupported_skill():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.skills["Tools"].append("Kubernetes")

    with pytest.raises(GroundingError, match="unsupported skills"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unknown_skill_category():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.skills["Cloud"] = ["AWS"]

    with pytest.raises(GroundingError, match="unknown skill category"):
        validate_grounding(master, tailored)


def test_fact_lookup_rejects_duplicate_fact_ids():
    master = _load_fixture("sample_master.json", MasterResume)
    master.experiences[1].facts[0].id = "BAB-01"

    with pytest.raises(ValueError, match="duplicate fact id"):
        master.fact_lookup()


def test_fact_rejects_invalid_id_format():
    with pytest.raises(ValidationError, match="fact id must match"):
        Fact(id="bad-id", text="Not a valid grounded fact id")


def test_master_resume_rejects_invalid_section_id():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    data["experiences"][0]["id"] = "bad-id"

    with pytest.raises(ValidationError, match="section id must be uppercase"):
        MasterResume(**data)


def test_master_resume_rejects_duplicate_section_ids():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    data["projects"][0]["id"] = "BAB"
    data["projects"][0]["facts"][0]["id"] = "BAB-04"
    data["projects"][0]["facts"][1]["id"] = "BAB-05"

    with pytest.raises(ValidationError, match="duplicate section id"):
        MasterResume(**data)


def test_master_resume_rejects_fact_id_outside_section_prefix():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    data["experiences"][0]["facts"][0]["id"] = "RS-01"

    with pytest.raises(ValidationError, match="fact ids must start with section id"):
        MasterResume(**data)


def test_build_grounding_report_marks_valid_bullets_supported():
    tailored = _load_fixture("sample_tailored.json", TailoredResume)

    report = build_grounding_report(tailored, 0.5, ["Python"], ["Kubernetes"])
    bullet_count = sum(
        len(section.bullets) for section in [*tailored.experiences, *tailored.projects]
    )

    assert report.match_score == 0.5
    assert report.matched_keywords == ["Python"]
    assert report.missing_keywords == ["Kubernetes"]
    assert report.grounding_ok is True
    assert len(report.verdicts) == bullet_count
    assert all(verdict.supported for verdict in report.verdicts)


def test_verdicts_carry_source_fact_ids():
    # the provenance panel reads these; without them it would have to parse
    # `% grounded:` comments out of the rendered tex
    tailored = _load_fixture("sample_tailored.json", TailoredResume)

    report = build_grounding_report(tailored, 0.0, [], [])
    cited = [
        bullet.source_fact_ids
        for section in [*tailored.experiences, *tailored.projects]
        for bullet in section.bullets
    ]

    assert [verdict.source_fact_ids for verdict in report.verdicts] == cited
    assert all(verdict.source_fact_ids for verdict in report.verdicts)


def test_validate_bridge_returns_supported_verdicts():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)

    grounding_ok, verdicts = validate(master, tailored)

    assert grounding_ok is True
    assert all(verdict.supported for verdict in verdicts)
    assert all(verdict.source_fact_ids for verdict in verdicts)


def test_validate_bridge_returns_failure_verdict():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[0].source_fact_ids = []

    grounding_ok, verdicts = validate(master, tailored)

    assert grounding_ok is False
    assert verdicts[0].supported is False
    assert "sourceless bullet" in verdicts[0].reason
