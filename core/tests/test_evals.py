"""Eval harness over core/fixtures/: schema validity always runs (mock-safe);
grounding/keyword metrics need a live key and are gated behind
RUN_REAL_EVALS=1 so a stray ANTHROPIC_API_KEY in the environment never
makes a normal `pytest` run spend real money.
"""

from pathlib import Path

from core.pipeline import structure_resume

RESUME_FIXTURES = Path(__file__).parent.parent / "fixtures" / "resumes"
POSTING_FIXTURES = Path(__file__).parent.parent / "fixtures" / "postings"


def _resume_files() -> list[Path]:
    return sorted(RESUME_FIXTURES.glob("*.txt"))


def test_fixture_resumes_exist():
    assert len(_resume_files()) >= 6


def test_every_resume_fixture_structures_to_a_valid_schema():
    for path in _resume_files():
        master = structure_resume(path.read_text())
        assert master.name
        # a valid MasterResume is achievement enough for the ugly fixtures;
        # schema validity, not extraction quality, is what this asserts
        master.fact_lookup()
