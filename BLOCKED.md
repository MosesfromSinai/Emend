# Blocked items

## RESOLVED: ANTHROPIC_API_KEY

A working, billable `ANTHROPIC_API_KEY` has been added (Moses, 2026-08-09).
The `401 authentication_error` originally hit in this shell was a Claude
Code session credential being used in place of a real Anthropic Console
key — those aren't interchangeable. With a real key in place, `MOCK=0`
real-mode paths (`parse_jd`/`tailor`/`judge_bullets`) should now work,
including `core/tests/test_evals.py::test_real_mode_grounding_and_keyword_coverage`
(`RUN_REAL_EVALS=1 EMEND_TRACE_PATH=<path> pytest core/tests/test_evals.py -k real_mode -s`)
and the cost-per-run numbers in `docs/evals.md`, still marked
`TODO(BLOCKED.md#real-mode)` there pending an actual run with the new key.

## RESOLVED (per Moses, pending live verification): Phase 4 (deploy) — Neon + Railway + Vercel are live

Deployed and serving: **https://emend-two.vercel.app** (web on Vercel, api on
Railway, Postgres on Neon). Details in `00-project-brief.md`'s "Deployment —
as built" section and `infra/runbook.md`.

Per Moses (2026-08-09): the Anthropic key above is set on Railway, and both
Railway and Vercel are up. `dynamic-resume` is fully merged into `main`
(confirmed via `git merge-base --is-ancestor`) as of PR #55, so `main` is
current with every fix through that PR.

**Not yet independently verified — do this next:** hit the live Railway API
URL's `/health` endpoint and run one real tailor request end-to-end to
confirm it's actually calling Claude (`MOCK=0`) rather than the mock
pipeline. Also worth a direct check (not just inference from "Railway is
up") that the CI→Railway auto-deploy workflow
(`.github/workflows/deploy.yml`) is actually succeeding on merges to `main`
now, rather than the site having been deployed by a manual `railway up` —
the earlier failure mode here was a missing `RAILWAY_TOKEN` GitHub secret.
