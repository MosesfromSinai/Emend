# Runbook — Emend platform (Workflow C)

## Local dev quickstart

```sh
# everything (once api/ and web/ exist):
docker compose -f infra/docker-compose.yml up --build
# web: http://localhost:3000 · api: http://localhost:8000 · postgres: :5432

# latex toolchain only (works today):
brew install tectonic uv           # one-time
uv venv --python 3.12 && uv pip install jinja2 pydantic pytest ruff
.venv/bin/python -m pytest latex/tests -q
```

Copy `infra/.env.example` → `infra/.env`. `MOCK=1` (default) needs no API key.

## Production setup (run once, in this order)

1. **Neon** — create a project + database. Copy the pooled connection string,
   then rewrite its scheme from `postgresql://` to **`postgresql+psycopg://`**
   before using it anywhere — SQLAlchemy picks its driver from the scheme, and
   the bare form resolves to psycopg2, which isn't installed.
2. **Railway** — from the repo root:
   ```sh
   railway login
   railway init                              # new project
   railway up --service Emend                 # builds infra/docker/api.Dockerfile
   railway volume add --mount-path /data --service Emend
   railway variables --service Emend \
     --set "DATABASE_URL=<neon-pooled-url>" \
     --set "CORS_ORIGINS=https://<vercel-domain>" \
     --set "SESSION_COOKIE_SAMESITE=none" \
     --set "SESSION_COOKIE_SECURE=1" \
     --set "ENVIRONMENT=production" \
     --set "MOCK=1"
   ```
   `ENVIRONMENT=production` turns off `/docs`/`/redoc`/`/openapi.json` and
   makes a missing `DATABASE_URL` fail startup loudly instead of silently
   falling back to the local-dev Postgres credentials.

   `Emend` is this project's actual Railway service name (Settings tab on the
   service card confirms it) — if you ever rename it or spin up a fresh
   project, update every `--service` flag here and in
   `.github/workflows/deploy.yml` to match, or `railway up`/`variables` will
   fail with "Service not found".

   Railway reads `infra/railway.json` for build + deploy config (point the
   service's *Config File Path* setting at it if it isn't picked up
   automatically). Set `ANTHROPIC_API_KEY` only when flipping to `MOCK=0`.

   Two deploy-time failure modes worth knowing before you hit them:
   - **No volume → failed deploy.** `requiredMountPath: "/data"` refuses to
     start without one. The `railway volume add` line above is not optional;
     500 MB is the plan cap and is plenty for artifacts.
   - **Healthcheck timeout → the port is wrong.** Railway assigns `$PORT` per
     deploy. `infra/docker/entrypoint.sh` passes `--port "${PORT:-8000}"`, so
     never reintroduce a hardcoded `--port` in the Dockerfile's `CMD`; it
     builds fine and then fails `/health` forever.
3. **GitHub** — repo → Settings → Secrets → Actions: add `RAILWAY_TOKEN`
   (Railway dashboard → project → Settings → Tokens → create a project
   token). After this, every green CI run on `main` auto-deploys the api via
   `.github/workflows/deploy.yml`.
4. **Vercel** — import the GitHub repo, set *Root Directory* to `web/`, add env
   `NEXT_PUBLIC_API_URL=https://<railway-api-domain>`. Vercel auto-deploys
   `main` and previews PRs; no workflow file needed.

## Secrets map

| Secret | Where it lives | Used by |
|---|---|---|
| `DATABASE_URL` | Railway variables, copied from Neon (prod) / compose env (dev) | api |
| `ANTHROPIC_API_KEY` | Railway variables (prod) / `.env` (dev, MOCK=0 only) | core via api |
| `RAILWAY_TOKEN` | GitHub Actions secrets | deploy workflow |
| `NEXT_PUBLIC_API_URL` | Vercel env / `.env` | web |

## Migrations on deploy

`infra/railway.json`'s `deploy.preDeployCommand` runs
`alembic -c api/alembic.ini upgrade head` against the new deployment before
it takes traffic; a failing migration aborts the deploy.

## LaTeX sandbox — how it's hardened

- `tectonic --untrusted` (+ `TECTONIC_UNTRUSTED_MODE=1`): shell-escape /
  `\write18` cannot be enabled, regardless of document content.
- Injection-safe escaping (`latex/escaping.py`) applied to **every** rendered
  string via Jinja's `finalize` hook — user text can never introduce a live
  LaTeX command.
- Hard subprocess timeout (`COMPILE_TIMEOUT_SECONDS`, default 10s) plus
  `RLIMIT_CPU`/`RLIMIT_AS` caps on the tectonic process.
- `TECTONIC_ONLY_CACHED=1` in the image: compiles never touch the network; the
  full package cache is baked into the image at build time
  (`infra/scripts/warm-tectonic-cache.py`), and CI proves it by compiling inside
  `docker run --network=none`.
- Non-root `appuser` in the image.
- The rendered `.tex` includes `% grounded: <fact ids>` receipt comments — they are
  product output (the proof artifact), not build noise. Never add comment
  stripping/minification anywhere in the pipeline; hostile ids are already
  whitespace-collapsed and escaped at render time so they can't break out of the
  comment.

## Reading a failed compile

`render_and_compile` returns `(tex, pdf_path, log)`; on failure `pdf_path` is
`""` and `log` holds Tectonic's full stdout/stderr (or a timeout message). The
api stores this on the application row; the web app surfaces it. Grep the log
for `error:` lines — the first one names the offending line in the generated
`.tex`.

## Rebuilding the Tectonic cache layer

If the template gains new packages (`\usepackage{...}`), the baked cache may
miss files and offline compiles will fail with `not found in cache`. Fix: any
change to `latex/` invalidates the Docker layer, so a plain rebuild re-warms the
cache — the build itself fails if the offline verification compile fails.

## Rollback

- **api:** Railway dashboard → service → Deployments → Redeploy a previous
  build (or re-run `.github/workflows/deploy.yml` from the last good commit).
- **web:** Vercel dashboard → Deployments → Promote a previous deployment.
- **db:** Neon supports point-in-time restore branches; create a branch at
  the pre-incident timestamp and repoint `DATABASE_URL`.

## Contract assumptions baked into infra (Workflow B/D, please confirm)

The Dockerfiles / compose / railway.json assume, per the brief's architecture:

- `api/requirements.txt` exists and includes `uvicorn` + `fastapi`; the app object
  is `api/main.py:app` (image CMD `uvicorn api.main:app`).
- The api exposes `GET /health` (railway.json's healthcheckPath hits it).
- The api reads `DATABASE_URL` (compose provides a psycopg3-style
  `postgresql+psycopg://` URL — adjust the driver suffix if B picks a different one)
  and writes PDFs under `ARTIFACTS_DIR` (`/data/artifacts` in prod, on the
  Railway volume).
- `web/` has standard `package.json` scripts (`dev`, `build`, `start`) and a
  committed `package-lock.json`.

If any of these differ, the fix belongs in `infra/` — ping Workflow C.

## Known gaps (updated 2026-08-03)

- **Production is deployed** (Vercel + Railway + Neon, `MOCK=1`) — see
  `00-project-brief.md`'s "Deployment — as built". `api/` and `web/` both
  exist and build; the paragraph above about them not existing is history,
  not current state.
- **CI→Railway auto-deploy is broken**: `.github/workflows/deploy.yml` fails
  every run with `Invalid RAILWAY_TOKEN` — the secret was never set. The live
  site was deployed some other way and may not match the latest `main`. Set
  `RAILWAY_TOKEN` in repo secrets and confirm the next merge redeploys.
- Branch protection on `main` is not configured on GitHub, despite the brief
  calling for it.
- Pixel-fidelity check against a real resume is pending — verification so far
  uses synthetic fixtures in `latex/tests/fixtures/`.
- The ~1–2s warm-compile target must be measured in the Linux image (macOS dev
  machines show ~3s of fontconfig/IO overhead not present in the container).
- PDF upload and job-URL ingestion are contract-decided (brief reconciliation
  #1) but not implemented anywhere in `api`/`web` — `core.extract.pdf_to_text`
  and `core.jd_text.html_to_jd_text` exist but nothing calls them outside
  `core`'s own tests.
