# Workflow A — Agent Pipeline & Evals

**Owner: Moses** · Directory: `core/` · Branches: `feat/core/*`
**Hand-off:** paste `00-project-brief.md` + this file into Claude Cowork; build only inside `core/`.

## Mission

Everything between raw user text and a validated, renderable resume object. In refactor mode, `structure_resume` is the star: messy pasted resume in, clean fact schema out. In tailor mode, the grounded pipeline is the product's differentiator. This workflow also owns the team-wide contracts, making it the architectural center of the system.

## Build list (implementation order)

1. `core/schemas.py` exactly as defined in the brief's Contracts, plus `MasterResume.all_fact_ids()` and `fact_lookup()` helpers.
2. `MOCK=1` mode: deterministic pass-through pipeline (no API key) so Workflows B/C/D are never blocked.
3. LLM wrapper: a single `structured_call(model, system, user, schema)` using forced tool-use so every call returns a validated Pydantic object; Sonnet for tailoring, Haiku for structuring/extraction/judging; prompt caching on the system prompt + master resume.
4. `structure_resume(text) -> MasterResume` — the refactor path's engine. Must produce clean schemas from all four teammates' real resumes plus two deliberately ugly test resumes.
5. `parse_jd(text) -> JDExtract` and deterministic `keyword_match(jd, master) -> (score, matched, missing)` — normalized string overlap, never the LLM.
6. `tailor(master, jd) -> TailoredResume` with hard prompt rules: every bullet cites `source_fact_ids`; rephrase/merge/reorder only; never add claims, numbers, or technologies not present in cited facts; leave JD gaps unfilled rather than bridging them.
7. Two-stage validation: structural pass (every cited id exists; no sourceless bullets), then the Haiku judge producing a `BulletVerdict` per bullet, rolled into `Report`.
8. Eval harness: `fixtures/` with ≥5 real postings; pytest metrics for grounding pass rate, keyword coverage, and schema validity; JSONL traces with token counts → documented cost per run.

## Interfaces

**Exposes:** typed functions consumed by Workflow B's background tasks.
**Consumes:** nothing — `core/` imports no other workflow and runs in plain pytest.
**Do not:** import FastAPI/Next/DB code into `core/`, compute match scores with the LLM, or let unvalidated output escape the pipeline.

## Acceptance criteria

Mock and real modes green in CI · clean schemas from all six test resumes · eval report on ≥5 postings with zero invented claims · cost per run documented.

## Resume bullets earned

- Architected a grounded LLM resume pipeline (Claude tool use, Pydantic-enforced structured outputs) that restructures raw resumes into verified fact schemas and tailors them to job postings without inventing claims
- Built a two-stage hallucination guard — deterministic fact-ID tracing plus an LLM-as-judge — achieving [X]% grounding pass rate across a [N]-posting eval suite with JSONL cost/latency tracing
- Defined shared data contracts and led system architecture for a 4-intern team (FastAPI, PostgreSQL, Next.js, LaTeX toolchain) on a deployed product
