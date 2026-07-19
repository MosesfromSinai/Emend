# Resume Tailor — Project Brief

**Team of 4 · new-grad SWE portfolio project · pair this brief with your individual workflow file when handing off to Claude Cowork.**

## Product definition

A deployed web app where a user pastes their resume, we **refactor it into clean Jake's-style LaTeX**, and they can **view it both ways** — rendered PDF and raw `.tex` — then **copy the LaTeX code** or **download/print the PDF**. Pasting a job description layers on the differentiating feature: a **tailored** version with a match score, keyword chips, and a provable no-invented-claims guarantee.

Two paths, one spine:

1. **Refactor path (no JD required):** paste resume → confirm extracted facts → clean LaTeX resume → dual view → copy `.tex` / download PDF.
2. **Tailor path:** paste a JD → tailored version with match score, keyword coverage, and a grounding report → same dual view and exports.

**Our wedge:** real `.tex` output the user keeps (not a builder they're trapped in), and provable grounding — every generated bullet cites the master-resume facts it came from; a validator rejects anything that doesn't trace back.

## How to use with Claude Cowork

Each member opens their workspace in Cowork and pastes **this brief + their own workflow file**, then instructs it to implement their build list **only inside their directories**, committing to branches with their prefix. PRs into protected `main` (green CI + 1 review). Contract changes are proposed, never merged unilaterally.

## In scope — the shippable product

Anonymous sessions (httpOnly cookie; no accounts) · paste-first resume import with an LLM-proposed fact schema gated by a **user confirmation screen** · refactor mode (no JD) · tailor mode (deterministic match score, hit/miss keyword chips, grounded rewriting, read-only provenance report) · dual-view workspace (react-pdf + copyable `.tex` pane) with PDF/`.tex` downloads and print · async job UX with status polling and surfaced compile logs on failure · history list with re-open/re-download · eval suite of ≥5 real postings with grounding pass rate, coverage, and cost per run reported in the README · deployed production URL · one-command local dev · CI on every PR · seed script · README with architecture diagram and demo GIF.

## Explicitly deferred — do NOT build

Application autofill / browser extension · accounts & auth · job-URL ingestion · PDF upload · per-bullet accept/reject editing and chat refinement · diff views · in-browser `.tex` editing · rate limiting · Redis/queues · additional templates · object storage.

## Architecture

**Components:** `web` (Next.js) → `api` (FastAPI + background tasks) → `core` (pure-Python LLM pipeline) + `latex` (render + sandboxed compile) → PostgreSQL.

**System flow:** Web calls `POST /applications {jd_text?}` (null = refactor mode). The API creates a row and launches a background task that runs the `core` pipeline — `parse_jd` → `keyword_match` → `tailor` → `validate`, all skipped in refactor mode — then calls `latex.render_and_compile`, saves `.tex`/PDF/report onto the row, and updates `status`. The web app polls `GET /applications/{id}` and presents the dual view.

**Grounding design (the differentiator):** the master resume is a set of atomic facts with ids. The tailor may only select, merge, rephrase, and reorder cited facts — every output bullet carries `source_fact_ids`. Validation is two-stage: a deterministic structural pass (every cited id exists; no sourceless bullets) and an LLM-as-judge pass (bullet content stays inside its cited facts). The match score is computed by normalized keyword overlap — never by the LLM — so the chips show exactly which terms hit.

## Stack — audited, one tool per job

**Languages:** Python 3.12 · TypeScript · SQL · LaTeX

| Layer | Choice | Workflow |
|---|---|---|
| LLM calls | `anthropic` SDK — tool-forced structured outputs; prompt caching; Sonnet tailors, Haiku structures/extracts/judges | A |
| Data contracts | Pydantic v2 — `core/schemas.py` is the single source of truth | A |
| Evals & tracing | pytest + `fixtures/` golden postings + JSONL trace/cost logs | A |
| API + jobs | FastAPI with background tasks + DB status polling | B |
| Database | PostgreSQL via SQLAlchemy 2 + Alembic; anonymous session scoping | B |
| LaTeX rendering | Jinja2 with `\VAR{}`/`\BLOCK{}` delimiters + injection-safe escaping | C |
| LaTeX compile | Tectonic `--untrusted`, pre-warmed cache, timeout/CPU/memory caps, non-root, in the api image | C |
| CI/CD & deploy | GitHub Actions · docker-compose (web, api, postgres) · Vercel + Fly.io/Railway + Neon | C |
| Frontend | Next.js App Router · Tailwind + shadcn/ui · react-pdf · plain `fetch` | D |

**Removed as redundant (team vote to re-add):** agent frameworks, Langfuse, promptfoo, TanStack Query/Zod, scraping libs, rank_bm25, slowapi, Redis/arq/Upstash, Auth.js/PyJWT, latexdiff, CodeMirror, WXT/Playwright, R2, PyMuPDF.

## Contracts — change only via a `contract` PR approved by all four

`core/schemas.py` (Pydantic v2, exact field names):
```python
Fact{id, text}
Experience{id, company, title, location, start, end, facts: list[Fact]}
Project{id, name, tech: list[str], facts: list[Fact]}
Education{school, degree, location, grad_date, coursework: list[str]}
MasterResume{name, email, phone, links: list[str], education: list[Education],
             experiences: list[Experience], projects: list[Project],
             skills: dict[str, list[str]]}
JDExtract{company, title, hard_skills, soft_requirements, responsibilities,
          keywords: list[str]}
TailoredBullet{text, source_fact_ids: list[str]}
TailoredSection{ref_id, bullets: list[TailoredBullet]}
TailoredResume{summary_of_strategy, experiences: list[TailoredSection],
               projects: list[TailoredSection], skills: dict[str, list[str]]}
BulletVerdict{bullet, supported: bool, reason}
Report{match_score: float, matched_keywords, missing_keywords,
       grounding_ok: bool, verdicts: list[BulletVerdict]}
```

API surface (the generated OpenAPI spec is the frontend's contract):
```
POST /resumes/import {text}          -> proposed MasterResume (not saved)
PUT  /resumes/master {MasterResume}  -> save confirmed   |   GET /resumes/master
POST /applications {jd_text?}        -> {id}   (null jd_text = refactor mode)
GET  /applications/{id}              -> status, match data, report, inline tex, artifact URLs
GET  /applications                   -> session's history
GET  /artifacts/{version_id}.pdf|.tex -> session-checked file response
```

LaTeX entrypoint: `latex.render_and_compile(master: MasterResume, tailored: TailoredResume | None) -> (tex: str, pdf_path: str, log: str)` — `tailored=None` renders the full master resume (refactor mode).

Database tables: `sessions(id, created_at)` · `master_resumes(id, session_id, data JSONB, updated_at)` · `applications(id, session_id, mode, jd_text NULL, status queued|running|done|failed, match_score, matched_keywords JSONB, missing_keywords JSONB, error, created_at)` · `resume_versions(id, application_id, tex TEXT, pdf_path, report JSONB, created_at)`.

**Mock rule:** `core` ships `MOCK=1` (deterministic pass-through, no API key). Every other workflow builds and tests against mock first, real later.

## Repo layout & conventions

```
resume-tailor/
├── core/    # Workflow A — schemas, prompts, pipeline, validators, evals (pure Python, zero web imports)
├── api/     # Workflow B — FastAPI, models, migrations, background jobs
├── latex/   # Workflow C — template, Jinja env, escaping, Tectonic wrapper
├── web/     # Workflow D — Next.js app
├── infra/   # Workflow C — Dockerfiles, compose, CI workflows
└── docs/    # this brief + the four workflow files + architecture diagram
```

`main` protected (green CI + 1 review) · branches `feat/<area>/<slug>` / `fix/<area>/<slug>` · conventional commits · rotate reviewers across workflows so everyone can whiteboard the whole system in interviews · never edit another workflow's directories · if it's not in a workflow file, it doesn't exist — claim it before building it.

## Non-functional requirements

Warm compiles ~1–2s with a hard timeout · no network egress from the compile step at runtime · every rendered string passes the escaping filter · input size limits on all text fields · session-scoped access on every query and artifact · works cleanly on a phone · fresh clone → one command → running app.

## Shared finish line

A stranger on the live URL pastes their resume, confirms the facts, and gets it refactored into LaTeX — viewable both ways, copyable, downloadable, printable — then pastes a JD and gets a tailored version with a match score and grounding report. The README carries the architecture diagram, usage GIF, and real eval numbers.

**Resume-honesty rule:** bullets go on our resumes when the thing they describe exists; bracketed numbers get filled in only once measured.
