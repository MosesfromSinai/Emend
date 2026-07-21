# Emend · Workflow B — Platform API & Data

**Owner: Teammate B** · Directory: `api/` · Branches: `feat/api/*`
**Hand-off:** paste `00-project-brief.md` + this file into Claude Cowork; build only inside `api/`.

## Mission

The stateful backbone: every byte that persists and every request the frontend makes goes through this workflow. It turns Workflow A's pure functions and Workflow C's compile step into a working product with sessions, jobs, and artifacts.

## Build list (implementation order)

1. FastAPI skeleton: routers, dependency-injected DB sessions, consistent JSON error shapes; runs in docker-compose.
2. SQLAlchemy 2 models + Alembic migrations for the four tables in the brief's Contracts; schema reproducible from zero.
3. Anonymous session middleware: httpOnly cookie issued on first visit; every query and artifact access scoped to that session. (No accounts — the landing page's account CTA copy is deferred with auth.)
4. Import flow: `POST /resumes/import` (calls `core.structure_resume`, returns the proposed schema unsaved), `PUT /resumes/master` (save confirmed), `GET /resumes/master`.
5. Job orchestration: `POST /applications {jd_text?}` creates the row and launches a FastAPI background task that runs `core` (skipping tailor when `jd_text` is null), calls `latex.render_and_compile`, saves tex/pdf/report to `resume_versions`, and updates `status`; `GET /applications/{id}` for polling; `GET /applications` for history.
6. Artifact serving: session-checked `.pdf`/`.tex` file responses plus inline `tex` (with its `% grounded:` comments intact) in the status payload for the frontend's copy pane.
7. Input size limits on every text field; a seed script with a sample resume + posting for instant local demos.

## Interfaces

**Exposes:** the REST API per the brief's Contracts — its OpenAPI spec is Workflow D's contract.
**Consumes:** `core` functions and `latex.render_and_compile`.
**Do not:** call the Anthropic API outside `core`, add auth or queues, build job-URL ingestion (deferred — the landing page's "paste a link" field is hidden/disabled until it ships), or serve artifacts without session checks.

## Acceptance criteria

An anonymous visitor completes both modes end-to-end through documented endpoints (import → confirm → run → poll → copy `.tex` → download PDF) · migrations reproduce from zero · seed script works.

## Resume bullets earned

- Designed the relational schema and migrations (PostgreSQL, SQLAlchemy 2, Alembic) for anonymous sessions, versioned resume schemas, and an async job lifecycle
- Built the FastAPI service orchestrating LLM structuring/tailoring and sandboxed LaTeX compilation via background tasks with status polling and session-scoped artifact serving
- Shipped human-in-the-loop resume import (LLM-proposed fact schema gated by user confirmation) on a deployed 4-person product
