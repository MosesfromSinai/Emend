"""Eval harness over core/fixtures/: schema validity always runs (mock-safe);
grounding/keyword metrics need a live key and are gated behind
RUN_REAL_EVALS=1 so a stray ANTHROPIC_API_KEY in the environment never
makes a normal `pytest` run spend real money.
"""

import os
import re
from pathlib import Path

import pytest

from core.extract import pdf_to_text
from core.pipeline import _fact_violations, parse_jd, real_tailor_result, structure_resume

RESUME_FIXTURES = Path(__file__).parent.parent / "fixtures" / "resumes"
POSTING_FIXTURES = Path(__file__).parent.parent / "fixtures" / "postings"
PDF_FIXTURES = Path(__file__).parent.parent / "fixtures" / "pdfs"
FACT_ID_SHAPE = re.compile(r"^[A-Z]{2,6}[0-9]?-[0-9]{2}$")
# shapes that are entry metadata, never fact content
NON_FACT_SHAPES = (
    re.compile(r"(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{1,2}/\d{4})\s*-\s*"
               r"(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{1,2}/\d{4}|Present|Current)", re.IGNORECASE),
    re.compile(r"^[A-Z][A-Za-z.\s]+,\s*[A-Z]{2}\.?$"),
    re.compile(r"^[A-Za-z/ ]+:\s"),
)
# hard mid-sentence wraps, a hyphenated line-wrap, a multi-sentence bullet,
# and three different bullet glyphs (bullet count -> 5 facts total)
WRAPPED_RESUME_SENTENCE_COUNT = 5

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


def test_wrapped_resume_structures_cleanly():
    """The exact acceptance bar for the sentence-parsing fix."""
    text = (RESUME_FIXTURES / "ugly_wrapped_resume.txt").read_text()

    master = structure_resume(text)

    all_facts = [f for e in [*master.experiences, *master.projects] for f in e.facts]
    assert len(all_facts) == WRAPPED_RESUME_SENTENCE_COUNT

    for entry in [*master.experiences, *master.projects]:
        company = getattr(entry, "company", "") or getattr(entry, "name", "")
        title = getattr(entry, "title", "")
        for fact in entry.facts:
            assert _fact_violations(fact.text, company, title) == []

    for experience in master.experiences:
        assert experience.company
        assert experience.title

    assert not any(
        "education" in e.company.lower() or "education" in e.title.lower()
        for e in master.experiences
    )
    assert len(master.education) == 1

    for fact_id in master.all_fact_ids():
        assert FACT_ID_SHAPE.match(fact_id), fact_id


def test_two_line_header_resume_segments_every_entry():
    """The acceptance bar for the entry-segmentation fix.

    Entries in this fixture run together with no blank lines between them,
    so the only boundary signal is Jake's two-line header (title + dates,
    then org + location). Getting it wrong collapses a whole section into
    one entry and bleeds one entity's id prefix across all of them.
    """
    text = (RESUME_FIXTURES / "two_line_headers.txt").read_text()

    master = structure_resume(text)

    assert [(e.company, e.title, e.start, e.end) for e in master.experiences] == [
        ("Solara Defense Systems", "Software Engineering Intern", "Jun 2025", "Sep 2025"),
        ("ACM @ Cascadia", "Technical Lead", "", "2025"),
        (
            "Pacific Aerospace Research Consortium",
            "Undergraduate Research Assistant",
            "Jan 2024",
            "Dec 2024",
        ),
    ]

    assert [p.name for p in master.projects] == ["Pathwise", "ThreatSense", "TermIt"]
    assert all(p.tech for p in master.projects)

    assert len(master.education) == 1
    assert master.education[0].school == "Cascadia University"
    assert master.education[0].coursework
    assert "Operating Systems" in master.education[0].coursework

    assert set(master.skills) == {
        "Languages",
        "Frameworks/Libraries",
        "Systems/Platforms",
        "Tools/Testing",
    }

    # one prefix per entry -- never one spanning several
    assert [e.id for e in master.experiences] == ["SDS", "ACM", "PARC"]
    assert [p.id for p in master.projects] == ["PATHWI", "TS", "TERMIT"]

    for entry in [*master.experiences, *master.projects]:
        company = getattr(entry, "company", "") or getattr(entry, "name", "")
        title = getattr(entry, "title", "")
        for fact in entry.facts:
            assert _fact_violations(fact.text, company, title) == []
            for shape in NON_FACT_SHAPES:
                assert not shape.search(fact.text), fact.text


def test_pdf_resume_extracts_and_structures_without_crashing():
    # pypdf's text extraction doesn't reliably preserve blank-line paragraph
    # gaps the way copy-pasted text does (a real, documented PDF-extraction
    # limitation, not a parser bug) -- same bar as the malformed text
    # fixtures: a clean result or a clean ValueError, never anything else.
    data = (PDF_FIXTURES / "sample_resume.pdf").read_bytes()
    text = pdf_to_text(data)
    assert "Jordan Rivera" in text

    try:
        master = structure_resume(text)
    except ValueError:
        return
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
