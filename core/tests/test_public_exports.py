import json
from pathlib import Path

import core
from core.schemas import JDExtract, MasterResume

FIXTURES = Path(__file__).resolve().parents[2] / "latex/tests/fixtures"


def test_core_exports_api_bridge_functions():
    expected = {
        "structure_resume",
        "parse_jd",
        "keyword_match",
        "refactor",
        "tailor",
        "validate",
    }

    assert expected <= set(core.__all__)
    assert all(callable(getattr(core, name)) for name in expected)


def test_core_structure_resume_export_is_callable():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    master = MasterResume(**data)

    assert core.structure_resume(master.model_dump_json()) == master


def test_core_exports_run_bridge_pipeline():
    master = core.structure_resume((FIXTURES / "sample_master.json").read_text())
    jd = JDExtract(
        company="",
        title="",
        hard_skills=[],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python"],
    )

    parsed_jd = core.parse_jd(jd.model_dump_json())
    tailored = core.tailor(master, parsed_jd)
    score, matched, missing = core.keyword_match(parsed_jd, master)
    grounding_ok, verdicts = core.validate(master, tailored)

    assert score == 1.0
    assert matched == ["Python"]
    assert missing == []
    assert grounding_ok is True
    assert all(verdict.supported for verdict in verdicts)
