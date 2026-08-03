# Blocked items

## Real-mode eval numbers need a working ANTHROPIC_API_KEY

**What's blocked:** `core/tests/test_evals.py::test_real_mode_grounding_and_keyword_coverage`
(gated behind `RUN_REAL_EVALS=1`) and the cost-per-run numbers in
`docs/evals.md` need a live, billable Anthropic API key to run
`parse_jd`/`tailor`/`judge_bullets` in real mode (`MOCK=0`) against the 5
posting fixtures in `core/fixtures/postings/`.

**What happened:** the `ANTHROPIC_API_KEY` present in this shell environment
returns `401 authentication_error: API key is invalid` when used directly
against the Anthropic Messages API via the `anthropic` Python SDK. It's
likely a Claude Code session credential rather than a standalone Anthropic
Console API key — those aren't necessarily interchangeable.

**What I need from you:** a valid `ANTHROPIC_API_KEY` from
console.anthropic.com (with billing enabled) exported in the shell, or
confirmation of where one already lives (e.g. `infra/.env`, a secrets
manager) that I should be reading from instead.

**What I did instead:** built the full eval harness so it runs the moment a
working key is available (`RUN_REAL_EVALS=1 EMEND_TRACE_PATH=<path> pytest
core/tests/test_evals.py -k real_mode -s`), and wrote `docs/evals.md` with
the report structure and every number marked `TODO(BLOCKED.md#real-mode)`
instead of guessing at figures. Everything else in this phase (schema
validity across fixtures, mock-mode tests, the trace writer itself) does
not need a key and is done and verified.

## RESOLVED: Phase 4 (deploy) — Neon + Railway + Vercel are live

Deployed and serving: **https://emend-two.vercel.app** (web on Vercel, api on
Railway, Postgres on Neon; `MOCK=1`, no working key yet — see the item above).
Details in `00-project-brief.md`'s "Deployment — as built" section and
`infra/runbook.md`.

**Still open:** the CI→Railway auto-deploy workflow
(`.github/workflows/deploy.yml`) is failing on every run with `Invalid
RAILWAY_TOKEN` — the repo has no `RAILWAY_TOKEN` secret set. The live site
was deployed some other way and isn't guaranteed to track the latest merged
`main`. Set the secret (Railway dashboard → project → Settings → Tokens) and
confirm the next merge actually redeploys.
