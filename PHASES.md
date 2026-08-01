# Phase 3 — Real mode + evals

Tracks work on the `harness` branch (Workflow A: core real-mode hardening
and eval harness, per `context/01-teammate-Moses.md` item 8).

## Done

- **Hardening** — core input size limits (`structure_resume`/`parse_jd`),
  module-level cached Anthropic client (keyed by API key), bounded parallel
  bullet judging (`ThreadPoolExecutor`, max 4 workers), `api/jobs.py`
  rollback-before-fail fix, decoupled `core/tests` fixtures off of
  `latex/tests/fixtures` into their own `core/tests/conftest.py`.
- **Eval posting fixtures** — 5 real, publicly posted new-grad SWE job
  descriptions fetched verbatim into `core/fixtures/postings/` (Nominal,
  Circle, Netic, Palantir, Databricks), each with source URL + fetch date.
- **Eval resume fixtures** — `core/fixtures/resumes/`: 4 synthetic (clearly
  labeled, not real people) resumes covering varied shapes/formatting, plus
  2 deliberately malformed ones. Verified all 6 parse without crashing
  through `structure_resume`'s mock-mode fallback.
- **JSONL trace writer** — `core/trace.py` (no-op unless `EMEND_TRACE_PATH`
  is set); `structure_resume`, `parse_jd`, `real_tailor_resume`, and
  `judge_bullets` now call `structured_call_with_usage` and record token
  counts per call instead of discarding usage data.
- **pytest eval harness** — `core/tests/test_evals.py`: schema-validity
  check runs every `pytest core/tests` across all 6 resume fixtures;
  grounding-rate/keyword-coverage check tailors the sample master against
  all 5 real postings, gated behind `RUN_REAL_EVALS=1` so an ambient
  `ANTHROPIC_API_KEY` never triggers real spend on a normal test run.
- **Cost-per-run doc** — `docs/evals.md` has the report structure and
  table; real numbers blocked, see `BLOCKED.md`.

**Blocked:** real-mode eval numbers need a working `ANTHROPIC_API_KEY` —
the one in this shell 401s against the real Messages API. Logged in
`BLOCKED.md`, TODO left in `core/tests/test_evals.py`. Skipping this piece
and moving on rather than guessing at numbers.

## In progress

- Real-`MOCK=1` integration test in `api` that exercises the actual core
  pipeline through the background job (not fully stubbed at `core_bridge`).

## Next

- Phase 4 (deploy) and anything else from the original roadmap once this
  branch is reviewed.
