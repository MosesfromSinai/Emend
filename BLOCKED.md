# Blocked items

Nothing currently blocked. Kept as a record of what was resolved and how it
was verified, in case the same class of issue comes up again.

## RESOLVED: ANTHROPIC_API_KEY / MOCK=0 in production

A working, billable `ANTHROPIC_API_KEY` was added on Railway and `MOCK=0`
is set (Moses, 2026-08-09). Confirmed live, not just inferred: the
production site has already served real tailoring requests. The earlier
`401 authentication_error` in this shell was a Claude Code session
credential mistakenly used in place of a real Anthropic Console key —
those aren't interchangeable; not an issue with the app itself.

Still open, not blocking: the cost-per-run numbers in `docs/evals.md` are
marked `TODO(BLOCKED.md#real-mode)` pending an actual
`RUN_REAL_EVALS=1 EMEND_TRACE_PATH=<path> pytest core/tests/test_evals.py -k real_mode -s`
run against the now-working key.

## RESOLVED: Phase 4 (deploy) — Neon + Railway + Vercel are live

Deployed and serving: **https://www.useemend.com** (web on Vercel) and
**https://emend-production.up.railway.app** (api on Railway), Postgres on
Neon. Details in `00-project-brief.md`'s "Deployment — as built" section
and `infra/runbook.md`.

Verified directly (2026-08-09), not just inferred from "Railway is up":
- `GET /health` → `200 {"status":"ok"}`
- `dynamic-resume` is fully merged into `main` (`git merge-base
  --is-ancestor dynamic-resume origin/main` → true) as of PR #55, so `main`
  is current through every fix landed there.
- `ENVIRONMENT=production` is now set on the Railway service. Before it was
  added, `/docs` and `/openapi.json` returned 200 (publicly exposed,
  unauthenticated); after adding it and redeploying, both return 404,
  confirmed live.
