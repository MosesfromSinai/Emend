"""Eval harness over core/fixtures/: schema validity always runs (mock-safe);
grounding/keyword metrics need a live key and are gated behind
RUN_REAL_EVALS=1 so a stray ANTHROPIC_API_KEY in the environment never
makes a normal `pytest` run spend real money.
"""

import os
from pathlib import Path

import pytest

from core.pipeline import parse_jd, real_tailor_result, structure_resume

RESUME_FIXTURES = Path(__file__).parent.parent / "fixtures" / "resumes"
POSTING_FIXTURES = Path(__file__).parent.parent / "fixtures" / "postings"

requires_real_evals = pytest.mark.skipif(
    os.getenv("RUN_REAL_EVALS") != "1",
    reason="set RUN_REAL_EVALS=1 (with a live ANTHROPIC_API_KEY) to run real-mode evals",
)


def _resume_files() -> list[Path]:
    return sorted(RESUME_FIXTURES.glob("*.txt"))


def test_fixture_resumes_exist():
    assert len(_resume_files()) >= 6


def test_every_resume_fixture_structures_without_crashing():
    # "structures cleanly" for well-formed resumes; for the deliberately
    # malformed ones, a clean ValueError from the structural validator is
    # an acceptable outcome too -- what must never happen is a fragment
    # fact slipping through, or any *other* kind of crash.
    for path in _resume_files():
        try:
            master = structure_resume(path.read_text())
        except ValueError:
            continue
        assert master.name
        master.fact_lookup()


def _posting_files() -> list[Path]:
    return sorted(POSTING_FIXTURES.glob("*.txt"))


# TODO(BLOCKED.md#real-mode-eval-numbers-need-a-working-anthropic_api_key):
# the ambient ANTHROPIC_API_KEY in this environment 401s against the real
# Messages API, so this has not been run for real yet -- run it once a
# working key is available and copy the numbers into docs/evals.md.
@requires_real_evals
def test_real_mode_grounding_and_keyword_coverage(sample_master, monkeypatch):
    monkeypatch.setenv("MOCK", "0")
    reports = [
        real_tailor_result(sample_master, parse_jd(path.read_text()))[1]
        for path in _posting_files()
    ]

    verdicts = [v for r in reports for v in r.verdicts]
    grounding_rate = sum(v.supported for v in verdicts) / len(verdicts)
    coverage = [
        len(r.matched_keywords) / max(1, len(r.matched_keywords) + len(r.missing_keywords))
        for r in reports
    ]

    print(
        f"postings={len(reports)} grounding_pass_rate={grounding_rate:.2f} "
        f"avg_keyword_coverage={sum(coverage) / len(coverage):.2f}"
    )
    # the two-stage guard (deterministic + judge) must reject anything short of this
    assert grounding_rate == 1.0
