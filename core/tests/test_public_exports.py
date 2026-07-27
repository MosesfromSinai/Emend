import json
from pathlib import Path

import core
from core.schemas import MasterResume

FIXTURES = Path(__file__).resolve().parents[2] / "latex/tests/fixtures"


def test_core_exports_api_bridge_functions():
    expected = {"structure_resume", "parse_jd", "keyword_match", "tailor", "validate"}

    assert expected <= set(core.__all__)
    assert all(callable(getattr(core, name)) for name in expected)


def test_core_structure_resume_export_is_callable():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    master = MasterResume(**data)

    assert core.structure_resume(master.model_dump_json()) == master
