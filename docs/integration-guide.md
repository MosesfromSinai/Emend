# Emend Integration Guide — how the four workflows come together

**Read this after** `context/00-project-brief.md` (product + contracts) and your own
workflow file (`context/01-teammate-Moses.md` / `02-Aldrie` / `03-Patrick` /
`04-Brandon`). This document covers what none of those do: the order things merge,
what already exists on `main`, what the platform assumes about your part, and how we
prove the seams work.

---

## 1. What exists on `main` today (Workflow C's platform PR)

| Path | What it is | Who owns it now |
|---|---|---|
| `core/schemas.py` | The brief's Pydantic contract, transcribed exactly — no helpers, no extras | **A (Moses)** from here on; C only bootstrapped it |
| `latex/` | Done: `render_and_compile()`, Jake's template, injection-safe escaping, `% grounded:` receipts on every bullet, sandboxed Tectonic wrapper, 27 tests | C (Patrick) |
| `infra/` | docker-compose, api/web Dockerfiles, cache-warm script, railway.json, runbook | C (Patrick) |
| `.github/workflows/` | CI (existence-guarded per area — your jobs auto-activate when your directory lands) + deploy | C (Patrick) |
| `ruff.toml`, `.gitignore` | Shared lint config (py312) and ignores | shared |

**CI is green on `main` right now.** The `test-core`, `test-api`, and `web-build`
jobs currently no-op with a "not present yet" message; the moment `core/tests/`,
`api/tests/`, or `web/package.json` exist, those jobs run for real and can fail
your PR. You do not need to touch CI to onboard.

---

## 2. What the platform already assumes about your part

These assumptions are baked into compose/Docker/railway.json. They're all standard, but
if your implementation differs, **say so before merging** — the fix belongs in
`infra/`, and it's cheap if C knows early.

**Workflow A (Moses, `core/`):**
- Pure Python, importable as `core.*` from the repo root; zero web/DB imports.
- Fact ids are the product's public face now: `<ENTITY>-<NN>` (`GA-01`, `NASA-01`),
  assigned by `structure_resume`, stable within a master-resume version. They appear
  verbatim in C's `% grounded:` receipts and D's fact-tag badges — please document
  the format in `core/schemas.py` when you add your helpers (C didn't edit your dir).
- `MOCK=1` env var switches the whole pipeline to deterministic, key-free mode.
  This is the single most load-bearing feature for everyone else — B's tests, D's
  dev loop, and CI all run against it. Build it first.
- `ANTHROPIC_API_KEY` is read only inside `core` (never by B directly).
- Add your `all_fact_ids()` / `fact_lookup()` helpers **onto the existing
  `core/schemas.py` models** — additive methods are a normal PR. Changing any
  field name/type is a `contract` PR requiring all four approvals.
- ⚠️ Ratify one judgment call: C typed `JDExtract.hard_skills / soft_requirements /
  responsibilities` and `Report.matched_keywords / missing_keywords` as
  `list[str]` (the brief left them untyped). If you want different shapes, raise
  it now via a contract PR before B/D depend on them.

**Workflow B (Aldrie, `api/`):**
- `api/requirements.txt` exists and includes `fastapi` + `uvicorn` (+ your DB deps).
- App object at `api/main.py:app` — the Docker image runs `uvicorn api.main:app`.
- Expose `GET /health` returning 200 — Railway's health check and compose depend on it.
- Read `DATABASE_URL` from env. Compose provides
  `postgresql+psycopg://emend:emend@postgres:5432/emend` (psycopg3 driver suffix —
  tell C if you pick psycopg2/asyncpg and we'll change compose, not you).
- Write PDFs under `ARTIFACTS_DIR` env (`/data/artifacts` in prod = the Railway volume;
  a named volume in compose). Store paths, serve files session-checked.
- `latex.render_and_compile(master, tailored|None) -> (tex, pdf_path, log)` is
  ready to call today. Failure mode: `pdf_path == ""` and `log` explains why (it
  never raises for compile failures/timeouts; it *does* raise `ValueError` on a
  tailored resume referencing unknown ids — treat that as a `failed` application
  with the message as `error`). Copy the PDF out of `pdf_path` into
  `ARTIFACTS_DIR`; the source lives in a temp dir.
- The returned `tex` carries `% grounded: <fact ids>` receipt comments above every
  bullet — they ARE the product ("the .tex is the proof artifact"). Store and serve
  it **verbatim**: no comment stripping, no reformatting, in both the inline `tex`
  field and the `.tex` artifact download. Receipts appear only on fact-backed
  experience/project bullets — coursework and skills are confirmed master data
  with no fact ids in the contract.
- Alembic: when you add migrations, also add the pre-deploy command to
  `infra/railway.json` (snippet ready in `infra/runbook.md`).

**Workflow D (Brandon, `web/`):**
- Standard Next.js layout in `web/` with `package.json` scripts `dev` / `build` /
  `start` and a committed `package-lock.json` (CI runs `npm ci`).
- The landing page is a **zero-dependency track**: it needs no API, no schemas,
  nothing from anyone — it can be your first PR and deploy to Vercel immediately.
  You'll need `Emend Landing v2.dc.html` (see Known gaps — it's not in the repo yet).
- Your fact-tag badges display the same `<ENTITY>-<NN>` ids the `.tex` receipts
  carry — one id vocabulary across the whole product.
- The API base URL comes from `NEXT_PUBLIC_API_URL` (compose sets
  `http://localhost:8000`; Vercel env sets the Railway URL).
- Session cookie is httpOnly and set by the API — send `credentials: 'include'`
  on every fetch; never store identity client-side.
- Until B's endpoints exist, build against the brief's API surface with
  handwritten types and a tiny fetch-mock layer; the response shapes are exactly
  the contract models in `core/schemas.py`.

---

## 3. Who blocks whom (and who doesn't)

```mermaid
graph LR
    D0[D: landing page — zero deps, ship anytime] --> E
    A1[A: MOCK pipeline] --> B2[B: job orchestration]
    C1[C: render_and_compile + receipts ✅] --> B2
    B1[B: FastAPI skeleton + models] --> B2
    B2 --> D2[D: live wiring]
    A2[A: real LLM pipeline] -.swap behind same interface.-> B2
    D1[D: app UI against mock shapes] --> D2
    B2 --> E[end-to-end in compose]
    D2 --> E
```

Key property of the design: **A's real LLM work and D's UI polish are never on the
critical path.** The mock pipeline + the finished latex layer mean B can build the
entire spine, and D the entire UI, without an API key or a finished prompt.

Nobody waits on anybody to *start*. The only hard joins are:
1. B's background task needs A's `MOCK=1` functions to exist (signatures + mock
   behavior only — not the real LLM).
2. D's live wiring needs B's endpoints (shapes are already known from the brief).

---

## 4. Merge order

Each numbered item is one or more PRs into protected `main` (green CI + 1 review,
conventional commits, branches `feat/<area>/<slug>`).

1. **C: platform bootstrap** *(this is what you're reviewing now)* — everything in
   section 1.
2. **A: `feat/core/schemas-and-mock`** — helper methods + `MOCK=1` deterministic
   pipeline (`structure_resume`, `parse_jd`, `keyword_match`, `tailor`, validators
   returning fixed-but-valid objects) + `core/tests/`. *Merging this unblocks B's
   spine and turns on the `test-core` CI job.*
3. **B: `feat/api/skeleton`** — FastAPI app + `/health` + session middleware +
   SQLAlchemy models + Alembic + compose boots. *Turns on `test-api` and the full
   api image CI build; from this point `docker compose up` is the team's
   integration harness.*
4. **D: `feat/web/landing`** — the Emend landing page from `Emend Landing v2.dc.html`
   + the Ink & Paper token foundation (Tailwind/shadcn on `--em-*` vars). Zero
   dependencies on A/B/C — can land any time, even before step 2, and gives us a
   deployed marketing URL on day one. *Turns on `web-build` CI.* Honor the brief's
   reconciliations: hide the "paste a link" field, reword the account CTA, no
   invented testimonials, demo content grounded in the sample resume.
5. **D: `feat/web/shell`** — app shell + onboarding UI against mock shapes.
6. **B: `feat/api/jobs`** — the orchestration: `POST /applications` → background
   task → `core` (mock) → `latex.render_and_compile` → `resume_versions` →
   status polling → artifact serving. **← Milestone: first true end-to-end.**
7. **D: `feat/web/live`** — swap mocks for real endpoints; dual view; async UX.
8. **A: `feat/core/real-llm`** — real Anthropic calls behind the same signatures;
   `MOCK=1` stays the CI default. Then `feat/core/evals` (fixtures, metrics, cost).
9. **C: deploy execution** — runbook's production setup (Neon → Railway → Vercel),
   secrets, first deploy, then keep `main` auto-deploying.
10. **All: hardening + README** (architecture diagram, demo GIF, eval numbers —
    the brief's "shared finish line").

Parallelism note: 2/3/4/5 can be in flight simultaneously (4 has zero
dependencies — it can even merge first); 6 needs 2+3 merged; 7 needs 6;
8 anytime after 2; 9 after 6 proves the spine (deploying the mock product
early is fine and encouraged — the landing page especially).

---

## 5. The runtime spine (what you're integrating toward)

```mermaid
sequenceDiagram
    participant W as web (D)
    participant API as api (B)
    participant CORE as core (A)
    participant LTX as latex (C)
    W->>API: POST /resumes/import {text}
    API->>CORE: structure_resume(text)
    CORE-->>W: proposed MasterResume (NOT saved)
    W->>API: PUT /resumes/master (user-confirmed)
    W->>API: POST /applications {jd_text?}
    API-->>W: {id}  (row status=queued)
    API->>CORE: parse_jd → keyword_match → tailor → validate (skipped if jd_text null)
    API->>LTX: render_and_compile(master, tailored|None)
    LTX-->>API: (tex, pdf_path, log)
    API->>API: save tex/pdf/report to resume_versions, status=done|failed
    loop until done/failed
        W->>API: GET /applications/{id}
    end
    W->>API: GET /artifacts/{version_id}.pdf|.tex
```

Failure contract along the spine: any stage that fails sets `status=failed` and a
human-readable `error` on the application row — compile failures carry the
Tectonic log so D can surface it verbatim. No silent failures, no stuck `running`.

---

## 6. Proving the seams — integration smoke tests

Run these at each milestone (they should eventually live in B's test suite):

**M0 (now):** `pytest latex/tests` green · sandbox image builds ·
`docker run --network=none <sandbox> python infra/scripts/warm-tectonic-cache.py`
compiles offline. (All enforced by CI already.)

**M1 (after merge-order step 6, MOCK=1, no keys needed):**
```
docker compose -f infra/docker-compose.yml up --build
# then, against http://localhost:8000:
POST /resumes/import   → 200, valid MasterResume JSON
PUT  /resumes/master   → 200; GET /resumes/master round-trips it
POST /applications {}                → id; poll until done; tex non-empty AND contains
                                       "% grounded:" receipts; pdf downloads
POST /applications {jd_text: "..."}  → done; report present; match_score is a float
GET  /artifacts/... without the session cookie → 403/404 (session scoping works)
```

**M2 (real mode):** same flow with `MOCK=0` + key; A's eval suite reports
grounding pass rate / coverage / cost on ≥5 postings.

**M3 (deployed):** the M1 flow against the production URL, from a phone.

---

## 7. Working agreements (recap + the two rules that prevent chaos)

- Branches `feat/<area>/<slug>` / `fix/<area>/<slug>`; conventional commits; PRs
  into protected `main` need green CI + 1 review; rotate reviewers across
  workflows (everyone should be able to whiteboard the whole system).
- **Never edit outside your directories.** The known shared surfaces and their
  owners: `core/schemas.py` → contract PR (all four approve) · `infra/` +
  `.github/` → C · `docs/` → whoever, review from the affected workflow.
- **If it's not in a workflow file, it doesn't exist.** Claim scope before
  building it; propose contract changes, never merge them unilaterally.
- Explicitly deferred (do not build, per the brief): auth/accounts, PDF upload,
  job-URL ingestion, rate limiting, Redis/queues, object storage, in-browser tex
  editing, diff views, per-bullet accept/reject, extra templates.

## 8. Open items needing a decision

| Item | Needs | Owner |
|---|---|---|
| `DATABASE_URL` driver suffix (`+psycopg` assumed) | confirm when picking DB lib | B |
| Railway project/service names | confirm at deploy time | C |

Closed:

- ✅ `JDExtract`/`Report` list fields typed `list[str]` — **ratified**, noted in `core/schemas.py`.
- ✅ Project dates — **accepted as-is**; the empty template slot is intentional, noted in `core/schemas.py`.
- ✅ Fact-id charset — documented in `core/schemas.py` and enforced by `FACT_ID_PATTERN`.
- ✅ Design files — committed under `docs/design/`; the demo persona is `docs/demo-persona.md`.
- ✅ `BulletVerdict.source_fact_ids` added so D's provenance panel reads fact ids
  from the `Report` instead of parsing `% grounded:` comments out of the tex.
