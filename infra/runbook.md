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

1. **Neon** — create a project + database. Copy the pooled connection string.
2. **Fly.io** — from the repo root:
   ```sh
   fly apps create emend-api                    # update app name in infra/fly.toml if different
   fly volumes create emend_artifacts --region sjc --size 1
   fly secrets set DATABASE_URL='<neon-url>' ANTHROPIC_API_KEY='<key>'
   fly deploy --config infra/fly.toml
   ```
3. **GitHub** — repo → Settings → Secrets → Actions: add `FLY_API_TOKEN`
   (`fly tokens create deploy`). After this, every green CI run on `main`
   auto-deploys the api via `.github/workflows/deploy.yml`.
4. **Vercel** — import the GitHub repo, set *Root Directory* to `web/`, add env
   `NEXT_PUBLIC_API_URL=https://emend-api.fly.dev`. Vercel auto-deploys `main`
   and previews PRs; no workflow file needed.

## Secrets map

| Secret | Where it lives | Used by |
|---|---|---|
| `DATABASE_URL` | Fly secrets (prod) / compose env (dev) | api |
| `ANTHROPIC_API_KEY` | Fly secrets (prod) / `.env` (dev, MOCK=0 only) | core via api |
| `FLY_API_TOKEN` | GitHub Actions secrets | deploy workflow |
| `NEXT_PUBLIC_API_URL` | Vercel env / `.env` | web |

## Migrations on deploy (for Workflow B to wire up)

Add to `infra/fly.toml` once Alembic exists in `api/`:

```toml
[deploy]
  release_command = "alembic -c api/alembic.ini upgrade head"
```

Release commands run against the new image before traffic switches; a failing
migration aborts the deploy.

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

- **api:** `fly releases --config infra/fly.toml` then
  `fly deploy --image <previous-image-ref>` (or re-run the deploy workflow from
  the last good commit).
- **web:** Vercel dashboard → Deployments → Promote a previous deployment.
- **db:** Neon supports point-in-time restore branches; create a branch at the
  pre-incident timestamp and repoint `DATABASE_URL`.

## Contract assumptions baked into infra (Workflow B/D, please confirm)

The Dockerfiles / compose / fly.toml assume, per the brief's architecture:

- `api/requirements.txt` exists and includes `uvicorn` + `fastapi`; the app object
  is `api/main.py:app` (image CMD `uvicorn api.main:app`).
- The api exposes `GET /health` (fly.toml's HTTP check hits it).
- The api reads `DATABASE_URL` (compose provides a psycopg3-style
  `postgresql+psycopg://` URL — adjust the driver suffix if B picks a different one)
  and writes PDFs under `ARTIFACTS_DIR` (`/data/artifacts` in prod, on the Fly
  volume).
- `web/` has standard `package.json` scripts (`dev`, `build`, `start`) and a
  committed `package-lock.json`.

If any of these differ, the fix belongs in `infra/` — ping Workflow C.

## Known gaps (updated 2026-07-19, post-Emend scope change)

- `api/` (Workflow B) and `web/` (Workflow D) don't exist yet: the compose `api`
  / `web` services and the full `runtime` Docker stage won't build until they
  land. `docker build --target latex-sandbox` and the `postgres` service work
  today.
- Pixel-fidelity check against all four teammates' real resumes is pending
  Workflow A's `structure_resume` (verification so far uses synthetic fixtures
  in `latex/tests/fixtures/`).
- Production deploy has not been executed yet — configs and this runbook are
  ready; run "Production setup" above when accounts/credentials are available.
- The ~1–2s warm-compile target must be measured in the Linux image (macOS dev
  machines show ~3s of fontconfig/IO overhead not present in the container).
