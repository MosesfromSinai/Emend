import json
from pathlib import Path

import pytest

from core.schemas import MasterResume, TailoredResume
from core.validation import GroundingError, validate_grounding

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


def test_validate_grounding_rejects_project_fact_on_experience():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[0].source_fact_ids = ["BERN-01"]

    with pytest.raises(GroundingError, match="outside-section ids"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unsupported_numbers():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[1].text = "Boosted processing throughput 95%"

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_low_fact_overlap():
    master = _load_fixture("sample_master.json", MasterResume)
    tailored = _load_fixture("sample_tailored.json", TailoredResume)
    tailored.experiences[0].bullets[0].text = "Led Kubernetes migrations for payment systems"

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
