# Eval report

Source: `core/tests/test_evals.py`, run against `core/fixtures/`.

## Schema validity (mock mode, runs in every `pytest core/tests`)

All 6 resume fixtures (4 synthetic, 2 deliberately malformed) structure to
a valid `MasterResume` with no crashes and no duplicate/malformed fact ids.
See `test_every_resume_fixture_structures_to_a_valid_schema`.

## Real-mode grounding + keyword coverage (needs a live key)

Run with:

```
RUN_REAL_EVALS=1 EMEND_TRACE_PATH=/path/to/trace.jsonl \
  pytest core/tests/test_evals.py -k real_mode -s
```

Tailors the shared sample master resume against all 5 real posting
fixtures in `core/fixtures/postings/` under `MOCK=0`, then reports:

| Metric | Value |
|---|---|
| Postings evaluated | TODO(BLOCKED.md#real-mode) |
| Grounding pass rate | TODO(BLOCKED.md#real-mode) |
| Avg. keyword coverage | TODO(BLOCKED.md#real-mode) |

## Cost per run (from JSONL trace data)

One `structure_resume` + one `parse_jd` + one `tailor` + N `judge_bullet`
calls per application (N = tailored bullet count). Per-call token counts
come straight from `EMEND_TRACE_PATH`; multiply by the current Anthropic
pricing for Haiku (structure/parse/judge) and Sonnet (tailor).

| Call | Model | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| structure_resume | Haiku | TODO(BLOCKED.md#real-mode) | TODO | TODO |
| parse_jd | Haiku | TODO | TODO | TODO |
| tailor | Sonnet | TODO | TODO | TODO |
| judge_bullet (avg) | Haiku | TODO | TODO | TODO |
| **Total per tailored application** | | | | **TODO** |
