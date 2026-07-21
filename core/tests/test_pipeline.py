import json
from pathlib import Path

from core.pipeline import mock_refactor_resume
from core.schemas import MasterResume
from core.validation import validate_grounding

FIXTURES = Path(__file__).resolve().parents[2] / "latex/tests/fixtures"


def _master() -> MasterResume:
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    return MasterResume(**data)


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
