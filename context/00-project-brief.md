# Emend — Project Brief

**Team of 4 · new-grad SWE portfolio project · pair this brief with your individual workflow file when handing off to Claude Cowork.**

## Product definition

**Emend** is AI-powered resume tailoring that **structurally cannot hallucinate**. Most resumes are filtered by ATS systems before a human reads them; Emend reverse-engineers that — it extracts what a posting prioritizes, then rewrites the user's resume to match (stronger verbs, quantified results, JD keywords), **constrained to facts the user confirmed**. The writer has no input except the confirmed fact list, and every generated line carries a receipt to its source fact (a `% grounded: GA-02` comment in the `.tex`). If a line has no source, it doesn't ship.

Hero line: *"A tailored resume that can't lie about you."*

Two paths, one spine:

1. **Refactor path (no JD required):** paste resume → confirm extracted facts → clean Jake's-style LaTeX → dual view (typeset PDF + `.tex` source) → copy `.tex` / download PDF.
2. **Tailor path:** paste a JD → grounded rewrite with match score, hit/miss keyword chips, and a grounding report → same dual view and exports.

**Our wedge:** real `.tex` output the user keeps, and provable grounding — every bullet cites `source_fact_ids`; a validator rejects anything that doesn't trace back.

## How to use with Claude Cowork

Each member pastes **this brief + their own workflow file** into Cowork and instructs it to implement their build list **only inside their directories**, committing to branches with their prefix. PRs into protected `main` (green CI + 1 review). Contract changes are proposed, never merged unilaterally.

## In scope — the shippable product

Anonymous sessions (httpOnly cookie; no accounts) · paste-first resume import with an LLM-proposed fact schema gated by a **user confirmation screen** · refactor mode (no JD) · tailor mode (deterministic match score, hit/miss keyword chips, grounded rewriting, read-only provenance report) · dual-view workspace (react-pdf + copyable `.tex` pane) with downloads and print · **the Emend landing page** (built from the v2 design component) · async job UX with polling and surfaced compile logs · history list · eval suite of ≥5 real postings with reported numbers · deployed production URL · one-command local dev · CI per PR · seed script · README with architecture diagram and demo GIF.

## Explicitly deferred — do NOT build

Application autofill / browser extension · accounts & auth · job-URL ingestion · PDF upload · **live** per-sentence rewrite cycling or accept/reject editing (the landing demo is scripted — see reconciliations) · chat refinement · diff views · in-browser `.tex` editing · rate limiting · Redis/queues · additional templates · object storage.

## Design system ("Ink & Paper")

**Design files (from Claude Design):** `Emend Landing v2.dc.html` (current landing — the implementation source), `Emend Landing.dc.html` (v1, history), `Resume Tailor Options.dc.html` (brand exploration; **1a "Ink & Paper" chosen**), `uploads/` (this brief + the sample resume PDF that grounds all demo content).

**Visual language:** paper background `#faf8f4`, ink `#1c1b18`, amber accent family `#8a6d1f` (soft `#f3ecd9`, bright `#c9a648`) · type: **Source Serif 4** (headings, resume body on the web), **JetBrains Mono** (fact tags, code, labels), system-ui (UI copy) · dark code panes `#211f1a` with amber LaTeX syntax highlighting · scroll-reveal on every section via IntersectionObserver (`[data-reveal]`) · tone: friendly, confident, job-seeker audience — the anti-hallucination story is the hero differentiator.

**Landing page v2 sections:** sticky blurred nav → hero (badge *structured generation · no hallucination by design*; product mock with JD-match card, keyword chips, 82 score ring, "grounded 18/18" pill, floating fact-tag badges; CTA pair + trust line) → proof strip → how-it-works (3 alternating steps) → **"Every sentence, your call"** interactive full-resume demo (scripted from the sample resume: click a sentence → toolbar → ‹ › cycles 3 grounded rewrites → "view my original" → inline edit while selected; every bullet shows its fact tag) → "Structured, so it can't hallucinate" pipeline diagram + stat cards (18/18, <60s, .tex) → testimonials, FAQ accordion, dark CTA band, footer.

**Theming/tweaks to preserve:** `colorScheme` (Amber default / Teal tide / Oxblood / Forest) swaps the accent family via `--em-*` CSS vars — all new elements must use `var(--em-accent|soft|softb|bright|deep, fallback)`; `revealMotion` (Subtle/Standard/Dramatic); `revealReplay`.

**Design conventions:** sample/demo content must stay grounded in the real resume in `uploads/` — never invent achievements. The web brand fonts do **not** change the LaTeX template: the typeset resume stays conventional (ATS-safe) — brand typography is web-only.

### Design ↔ scope reconciliations (team decisions, decided now)

1. **"Paste a link to the posting" field (hero + step 01):** job-URL ingestion is deferred — hide the field or disable it with a "coming soon" tooltip until it ships.
2. **Dark CTA band "Create a free account…":** accounts are deferred — reword the CTA (v1 is anonymous sessions); account copy returns when auth ships.
3. **Interactive sentence-rewrite demo:** on the landing page it is **scripted** (three pre-written grounded rewrites per sentence, ported from the design component). Live per-sentence cycling in the workspace is post-MVP.
4. **Testimonials:** ship only real quotes. Invented testimonials would violate the product's own no-invented-claims brand — drop or replace the section until real users exist.

## Architecture

**Components:** `web` (Next.js) → `api` (FastAPI + background tasks) → `core` (pure-Python LLM pipeline) + `latex` (render + sandboxed compile) → PostgreSQL.

**System flow:** Web calls `POST /applications {jd_text?}` (null = refactor mode). The API creates a row and launches a background task that runs the `core` pipeline — `parse_jd` → `keyword_match` → `tailor` → `validate`, all skipped in refactor mode — then calls `latex.render_and_compile`, saves `.tex`/PDF/report onto the row, and updates `status`. The web app polls `GET /applications/{id}` and presents the dual view.

**Grounding design:** the master resume is a set of atomic facts with **human-readable ids** (`GA-01`, `ACM-02`, `NASA-01` — `<ENTITY>-<NN>`, assigned at structuring). The tailor may only select, merge, rephrase, and reorder cited facts — every output bullet carries `source_fact_ids`. Validation is two-stage: deterministic structural pass, then LLM-as-judge. The rendered `.tex` carries the receipts: a `% grounded: GA-01, GA-02` comment above each bullet. Match score is normalized keyword overlap — never the LLM.

## Stack — audited, one tool per job

**Languages:** Python 3.12 · TypeScript · SQL · LaTeX

| Layer | Choice | Workflow |
|---|---|---|
| LLM calls | `anthropic` SDK — tool-forced structured outputs; prompt caching; Sonnet tailors, Haiku structures/extracts/judges | A |
| Data contracts | Pydantic v2 — `core/schemas.py` is the single source of truth | A |
| Evals & tracing | pytest + `fixtures/` golden postings + JSONL trace/cost logs | A |
| API + jobs | FastAPI with background tasks + DB status polling | B |
| Database | PostgreSQL via SQLAlchemy 2 + Alembic; anonymous session scoping | B |
| LaTeX rendering | Jinja2 with `\VAR{}`/`\BLOCK{}` delimiters + injection-safe escaping + grounding comments | C |
| LaTeX compile | Tectonic `--untrusted`, pre-warmed cache, timeout/CPU/memory caps, non-root, in the api image | C |
| CI/CD & deploy | GitHub Actions · docker-compose (web, api, postgres) · Vercel + Fly.io/Railway + Neon | C |
| Frontend | Next.js App Router · Tailwind + shadcn/ui on the Ink & Paper tokens · react-pdf · plain `fetch` | D |

**Removed as redundant (team vote to re-add):** agent frameworks, Langfuse, promptfoo, TanStack Query/Zod, scraping libs, rank_bm25, slowapi, Redis/arq/Upstash, Auth.js/PyJWT, latexdiff, CodeMirror, WXT/Playwright, R2, PyMuPDF.

## Contracts — change only via a `contract` PR approved by all four

`core/schemas.py` (Pydantic v2, exact field names; fact ids are `<ENTITY>-<NN>` strings):
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

LaTeX entrypoint: `latex.render_and_compile(master: MasterResume, tailored: TailoredResume | None) -> (tex: str, pdf_path: str, log: str)` — `tailored=None` renders the full master resume; rendered bullets carry `% grounded: <fact ids>` comments.

Database tables: `sessions(id, created_at)` · `master_resumes(id, session_id, data JSONB, updated_at)` · `applications(id, session_id, mode, jd_text NULL, status queued|running|done|failed, match_score, matched_keywords JSONB, missing_keywords JSONB, error, created_at)` · `resume_versions(id, application_id, tex TEXT, pdf_path, report JSONB, created_at)`.

**Mock rule:** `core` ships `MOCK=1` (deterministic pass-through, no API key). Every other workflow builds against mock first, real later.

## Repo layout & conventions

```
emend/
├── core/    # Workflow A — schemas, prompts, pipeline, validators, evals (pure Python, zero web imports)
├── api/     # Workflow B — FastAPI, models, migrations, background jobs
├── latex/   # Workflow C — template, Jinja env, escaping, Tectonic wrapper
├── web/     # Workflow D — Next.js app + landing page
├── infra/   # Workflow C — Dockerfiles, compose, CI workflows
└── docs/    # this brief, the four workflow files, design components, architecture diagram
```

`main` protected (green CI + 1 review) · branches `feat/<area>/<slug>` / `fix/<area>/<slug>` · conventional commits · rotate reviewers across workflows · never edit another workflow's directories · if it's not in a workflow file, it doesn't exist — claim it before building it.

## Non-functional requirements

Warm compiles ~1–2s with a hard timeout · no network egress from the compile step at runtime · every rendered string passes the escaping filter · input size limits on all text fields · session-scoped access on every query and artifact · works cleanly on a phone · fresh clone → one command → running app.

## Shared finish line

A stranger lands on the Emend page, pastes their resume, confirms the facts, and gets it refactored into LaTeX — viewable both ways, copyable, downloadable, printable — then pastes a JD and gets a tailored version with a match score and grounding report, receipts visible in the `.tex`. The README carries the architecture diagram, usage GIF, and real eval numbers.

**Resume-honesty rule:** bullets go on our resumes when the thing they describe exists; bracketed numbers get filled in only once measured. Same rule the product enforces on itself.
