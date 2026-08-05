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

Anonymous sessions (httpOnly cookie; no accounts) · paste-first resume import with an LLM-proposed fact schema gated by a **user confirmation screen**, accepting either pasted text or a **PDF upload** · refactor mode (no JD) · tailor mode (deterministic match score, hit/miss keyword chips, grounded rewriting, read-only provenance report), fed by either pasted JD text or a **job-posting URL** (fetched and extracted server-side) · dual-view workspace (react-pdf + copyable `.tex` pane) with downloads and print · **the Emend landing page** (built from the v2 design component, responsive) · async job UX with polling and surfaced compile logs · history list · eval suite of ≥5 real postings with reported numbers · deployed production URL · one-command local dev · CI per PR · seed script · README with architecture diagram and demo GIF.

## Explicitly deferred — do NOT build

Application autofill / browser extension · accounts & auth · **live** per-sentence rewrite cycling or accept/reject editing in the workspace (the landing demo is scripted — see reconciliations) · chat refinement · diff views · in-browser `.tex` editing · rate limiting · Redis/queues · additional templates · object storage.

## Design system ("Ink & Paper")

**Design files (from Claude Design):** `Emend Landing v2.dc.html` (current landing — the implementation source), `Emend Landing.dc.html` (v1, history), `Resume Tailor Options.dc.html` (brand exploration; **1a "Ink & Paper" chosen**), `uploads/` (project brief; the real resume PDF there is a private eval fixture only — all demo content now grounds to `docs/demo-persona.md`).

**Visual language:** paper background `#faf8f4`, ink `#1c1b18`, amber accent family `#8a6d1f` (soft `#f3ecd9`, bright `#c9a648`) · type: **Source Serif 4** (headings, resume body on the web), **JetBrains Mono** (fact tags, code, labels), system-ui (UI copy) · dark code panes `#211f1a` with amber LaTeX syntax highlighting · scroll-reveal on every section via IntersectionObserver (`[data-reveal]`) · tone: friendly, confident, job-seeker audience — the anti-hallucination story is the hero differentiator.

**Landing page v2 sections:** sticky blurred nav → hero (badge *structured generation · no hallucination by design*; product mock with JD-match card + blinking cursor, keyword chips, 82 score ring, "grounded 18/18" pill, floating fact-tag badges; CTA pair + trust line) → proof strip → how-it-works (3 alternating steps) → **"Every sentence, your call"** interactive full-resume demo with a floating "↓ try it — click any sentence below" hint pill; click a sentence → block highlights + dark toolbar: ‹ › cycles 3 grounded rewrites (dots indicator), "view my original" reverts to the original wording ("↩ back to my edit / Emend's rewrite" returns), and text is **click-to-edit for real** — typing shows "↺ discard my edit" instantly, blur/Enter saves (tag flips to "edited ✎", label "your edit · based on fact GA-01"), cycling or discard replaces it; click off to deselect; every bullet shows its fact tag, flipping to "original" on revert → "Structured, so it can't hallucinate" pipeline diagram + stat cards (18/18, <60s, .tex) → testimonials, FAQ accordion, dark CTA band, footer.

**Demo implementation notes (from the design component):** sentence state updates use functional setState (stale-closure race fix); the contenteditable span carries a state-derived `key` so text remounts when its source changes.

**Responsive spec:** the design component achieves responsiveness via media queries + `.em-*` utility classes (`!important` over inline styles); the Next.js port translates these into Tailwind responsive utilities while preserving the behavior — **≤960px:** hero & workflow steps collapse to 1 column (text first), pipeline stacks with rotated arrows, testimonials stack, footer 2-col; **≤680px:** smaller headings, nav anchors hidden (logo + Get started stay), tighter section padding, resume card slims, stats/CTA/step-3 rows stack, floating hero badges hidden, footer 1-col; `overflow-x: hidden` on html/body.

**Theming/tweaks to preserve:** `colorScheme` (Amber default / Teal tide / Oxblood / Forest) swaps the accent family via `--em-*` CSS vars — all new elements must use `var(--em-accent|soft|softb|bright|deep, fallback)`; `revealMotion` (Subtle/Standard/Dramatic); `revealReplay`.

**Design conventions:** demo/sample content must stay grounded in the fact file that sources it — never invent achievements. The web brand fonts do **not** change the LaTeX template: the typeset resume stays conventional (ATS-safe) — brand typography is web-only.

### Design ↔ scope reconciliations (team decisions)

1. **"Paste a link to the posting" field (hero + step 01) — SHIPPED.** Job-URL ingestion is fully wired: `CreateApplicationRequest` and the `applications` table both carry `jd_url` alongside `jd_text` (never both — 422 if both are set), `api/jobs.py` fetches it server-side with a browser-like `User-Agent` (bot-protection CDNs in front of major careers sites silently drop requests without one), extracts JD text via `core.jd_text.html_to_jd_text` (also reads schema.org `JobPosting` JSON-LD for JS-rendered SPA shells, and strips "Related Jobs"-style carousels and nav/CTA links that otherwise leak into the extracted text), and runs the normal `parse_jd` pipeline. `GET /applications/{id}` reports `jd_source_url`. Same for PDF upload: `POST /resumes/import` accepts both a JSON `{text}` body and a multipart `file=<pdf>` upload. The Tailor screen's live score card (`POST /jd/preview`) takes the same `jd_text`/`jd_url` pair for a cheap parse+match-only preview.
2. **Dark CTA band "Create a free account…":** accounts are deferred — reword the CTA (v1 is anonymous sessions); account copy returns when auth ships.
3. **Interactive sentence demo:** on the landing page it is **scripted** (three pre-written grounded rewrites per sentence, ported from the design component; the click-to-edit behavior is real but client-side only). Live per-sentence cycling in the workspace is post-MVP.
4. **Testimonials:** ship only real quotes. Invented testimonials would violate the product's own no-invented-claims brand — drop or replace the section until real users exist.
5. **Demo resume source — DECIDED: fictional persona.** The landing demo and hero mock are built from the **Sam Reyes** persona in `docs/demo-persona.md` (same resume shape as the original demo content; ids like `HX-01`), so no real contact info, employer names, or implied endorsements ship on the marketing page. The real resume stays private as a Workflow A eval fixture. The "never invent" convention reads: every demo sentence and rewrite traces to the persona fact file.

## Architecture

**Components:** `web` (Next.js) → `api` (FastAPI + background tasks) → `core` (pure-Python LLM pipeline) + `latex` (render + sandboxed compile) → PostgreSQL.

**System flow:** Web calls `POST /applications {jd_text?}` (null = refactor mode). The API creates a row and launches a background task that runs the `core` pipeline — `parse_jd` → `keyword_match` → `tailor` → `validate`, all skipped in refactor mode — then calls `latex.render_and_compile`, saves `.tex`/PDF/report onto the row, and updates `status`. The web app polls `GET /applications/{id}` and presents the dual view.

**Grounding design:** the master resume is a set of atomic facts with **human-readable ids** (`GA-01`, `ACM-02`, `NASA-01` — `<ENTITY>-<NN>`, assigned at structuring). The tailor may only select, merge, rephrase, and reorder cited facts — every output bullet carries `source_fact_ids`. Validation is two-stage: deterministic structural pass, then LLM-as-judge. The rendered `.tex` carries the receipts: a `% grounded: GA-01, GA-02` comment above each bullet. Match score is normalized keyword overlap — never the LLM. **No derived numbers:** a bullet may not emit any numeric token — integer, decimal, percentage, or duration — that does not appear literally in the text of its cited facts. No percentages computed from two stated values, no deltas, no subtractions, no rounding; rephrase to carry the facts' own numbers instead. This is a deterministic, structural-pass rule, not a judge call — "the arithmetic is correct" is not the same claim as "the number is grounded," and only the former is machine-checkable without an LLM.

## Stack — audited, one tool per job

**Languages:** Python 3.12 · TypeScript · SQL · LaTeX

| Layer | Choice | Workflow |
|---|---|---|
| LLM calls | `anthropic` SDK — tool-forced structured outputs; prompt caching; Sonnet tailors, Haiku structures/extracts/judges | A |
| Data contracts | Pydantic v2 — `core/schemas.py` is the single source of truth | A |
| Evals & tracing | pytest + `fixtures/` golden postings + JSONL trace/cost logs | A |
| Resume/JD ingestion | `pypdf` (PDF text extraction) + `selectolax` (HTML → JD text) in `core/`, offline and pure Python | A |
| API + jobs | FastAPI with background tasks + DB status polling; `httpx` for server-side job-posting URL fetch | B |
| Database | PostgreSQL via SQLAlchemy 2 + Alembic; anonymous session scoping | B |
| LaTeX rendering | Jinja2 with `\VAR{}`/`\BLOCK{}` delimiters + injection-safe escaping + grounding comments | C |
| LaTeX compile | Tectonic `--untrusted`, pre-warmed cache, timeout/CPU/memory caps, non-root, in the api image | C |
| CI/CD & deploy | GitHub Actions · docker-compose (web, api, postgres) · **Vercel (web) + Railway (api) + Neon (Postgres)** — deployed, see below | C |
| Frontend | Next.js App Router · Tailwind + shadcn/ui on the Ink & Paper tokens · react-pdf · plain `fetch` | D |

**Removed as redundant:** agent frameworks, Langfuse, promptfoo, TanStack Query/Zod, rank_bm25, slowapi, Redis/arq/Upstash, Auth.js/PyJWT, latexdiff, CodeMirror, WXT/Playwright, R2. (`scraping libs` and `PyMuPDF` were on this list when job-URL ingestion and PDF upload were deferred; superseded above by `selectolax` and `pypdf` respectively now that both are in scope.)

## Deployment — as built

Live: **https://emend-two.vercel.app**. Three attached backing services, each
owned by whoever runs it, none bundled into another (twelve-factor: a backing
service is an attached resource, swappable by changing one URL).

| Piece | Where | How it's wired |
|---|---|---|
| `web` | **Vercel** | GitHub repo import, *Root Directory* `web/`, auto-deploys on `main`. Env: `NEXT_PUBLIC_API_URL` → the Railway api domain. |
| `api` + `latex` | **Railway** | One service built from `infra/docker/api.Dockerfile`; config lives in `infra/railway.json` (healthcheck `/health`, `preDeployCommand` runs `alembic upgrade head`, restart-on-failure). A **500 MB volume mounted at `/data`** holds compiled artifacts — `requiredMountPath` fails the deploy if it's missing. |
| Postgres | **Neon** | Separate project; its pooled connection string goes into Railway's `DATABASE_URL`. Neon hands out `postgresql://…`; the app's SQLAlchemy driver needs it rewritten to **`postgresql+psycopg://…`** before pasting. |

Two things that bit us and stay true of any redeploy:

- **The container must listen on the platform's `$PORT`, not a hardcoded one.**
  Railway assigns it per deploy; `infra/docker/entrypoint.sh` ends in
  `exec gosu appuser "$@" --port "${PORT:-8000}"` so the Dockerfile's `CMD`
  never pins it. A hardcoded port passes the build and fails the healthcheck.
- **Artifacts need a real volume.** `/data` is where `api/jobs.py` writes; with
  no volume attached the mount path check fails the deploy outright, which is
  the loud failure we want rather than losing artifacts on restart.

Currently running **`MOCK=1`** — no working `ANTHROPIC_API_KEY` yet, so what
production actually exercises is the deterministic parser and the mock
tailorer. Flipping to `MOCK=0` is a Railway variable change once the key
works and the evals in `docs/evals.md` have real numbers.

**Auto-deploy:** fixed 2026-08-03 (`RAILWAY_TOKEN` set, service name
corrected in `.github/workflows/deploy.yml` to match Railway's actual
service name `Emend`). Verified green end to end: CI → Deploy → `/health`.

Operational detail — secrets map, migrations, rollback per service, rebuilding
the Tectonic cache layer — lives in `infra/runbook.md`.

## App screens rebuild — done on branch `import-tailor`, not yet merged to main

Full plan at `/Users/mosesavila/.claude/plans/glowing-popping-giraffe.md`
(local machine, not in-repo) — all 7 parts complete as of 2026-08-04: 3 real
grounded rewrite variants per tailored bullet (`TailoredBullet.text` →
`.variants: list[str]`, a contract change — validation/judging run per
variant, `render_tex`/`render_and_compile` take a `selections` override map),
the app shell + design tokens, and all four post-"Get started" screens
(Import, Confirm facts, Tailor, Export) rebuilt per `Emend App.dc.html` in
the Claude Design project — Confirm has real per-fact confirmation with a
bidirectional paper↔panel hover sync, Tailor has a live debounced
`/jd/preview` score card, Export has real 3-variant rewrite cycling backed
by `/applications/{id}/preview` (live) and `/finalize` (on download).
Accounts stay explicitly deferred per this brief's existing scope — nothing
in this work adds auth. Single branch, phased commits, not yet PR'd/merged.

**Tailor pipeline hardening — same branch, 2026-08-04.** Keyword extraction
was reworked from a curated skills dictionary to literal, deterministic
phrase extraction straight from the posting's own text
(`core/matching.py::extract_keywords`) — never an LLM, never a fixed list,
so coverage isn't capped by whatever someone thought to add ahead of time.
JD-URL fetch reliability was hardened (browser User-Agent, JSON-LD
extraction for JS-only postings, page-chrome stripping — see reconciliation
#1 above) and a link pasted into the text field, or a posting text with no
extractable keywords, now fails with a clear 422 instead of silently
scoring a fake 0%. `real_tailor_resume` retries a grounding rejection with
the specific violation fed back to the model instead of failing the whole
job over one invented number. The Tailor screen's score card is reframed
end to end as a compatibility read (`{pct}% · Strongly compatible` /
`{pct}% · Compatible, with N real gap(s)`, never "Needs work"), and
`TAILOR_SYSTEM` now says explicitly that reordering skills and bullets per
posting is the point of tailoring, not optional polish, plus a self-check
step and an explicit "the posting is ordering-only, never a content
source" instruction.

**Audit round, same day.** An adversarial code review turned up and fixed six
real grounding/matching bugs: `tailor()`'s public entrypoint wasn't actually
gated on the stage-2 LLM judge (a judge-rejected bullet could still ship in
the exported PDF — now `enforce_judge=True` in real mode, with the same
retry-with-feedback treatment as a stage-1 rejection); `drop_known_names`
dropped a real skill whenever it was merely a substring of the job title
(e.g. "Java" inside "Java Developer" — now exact-match against the title
and its comma/dash-separated segments only); `_numeric_tokens` was blind to
a same-digit unit/magnitude swap ("20ms" restated as "20 seconds" passed
grounding cleanly — now unit-tagged); `keyword_match` matched a multi-word
keyword via a whole-resume bag of words, so "Team Leadership Experience"
could match three unrelated facts that each contributed one word (now
matched per-unit — one fact/skill/project span at a time); `_validate_skills`
checked a tailored skill against a flattened set across every category
instead of its own, so a skill could be silently relabeled into the wrong
category; and `render_tex` fell back to the full master skills block
whenever a tailor call correctly decided no skill category was relevant
(`{}` is falsy in Python) instead of honoring that as a real decision.
**Known gap, not yet resolved:** the ANTHROPIC_API_KEY in the local dev
shell is rejected by Anthropic's API (401), so live empirical verification
that real-mode tailoring actually reorders content differently per posting
is blocked pending a working key — prompt-level instructions and unit
tests are in place, but this hasn't been confirmed against the real model.

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
          keywords: list[str], source_url: str | None = None}
TailoredBullet{variants: list[str] (exactly 3, non-empty), source_fact_ids: list[str]}
TailoredSection{ref_id, bullets: list[TailoredBullet]}
TailoredResume{summary_of_strategy, experiences: list[TailoredSection],
               projects: list[TailoredSection], skills: dict[str, list[str]]}
BulletVerdict{bullet, supported: bool, reason}
Report{match_score: float, matched_keywords, missing_keywords,
       grounding_ok: bool, verdicts: list[BulletVerdict]}
```

API surface (the generated OpenAPI spec is the frontend's contract):
```
POST /resumes/import {text} | multipart file=<pdf>
                                      -> proposed MasterResume (not saved), either way
PUT  /resumes/master {MasterResume}  -> save confirmed   |   GET /resumes/master
POST /applications {jd_text?, jd_url?} -> {id}   (both null = refactor mode; both set = 422)
GET  /applications/{id}              -> status, match data, report, inline tex, tailored resume,
                                         artifact URLs, jd_source_url (null unless from a URL)
POST /applications/{id}/preview {selections} -> {tex}  cheap re-render, no compile (Export's live pane)
POST /applications/{id}/finalize {selections} -> version out, real compile (runs once, on download)
GET  /applications                   -> session's history
GET  /artifacts/{version_id}.pdf|.tex -> session-checked file response
POST /jd/preview {jd_text?, jd_url?} -> {score, matched_keywords, missing_keywords, resolved_jd_text}
                                         parse_jd + keyword_match only, no tailor call (Tailor's live score card)
```
`selections` is `dict[fact_id, {variant_idx?: 0-2, custom_text?}]` — keyed by a bullet's first
`source_fact_ids` entry; no entry for a bullet renders its first variant.
`POST /resumes/import`'s multipart path and `jd_url` fetch/extraction are contract-documented here now; implementation is a later task, not part of this change — see reconciliation #1 above for exactly what's built vs. not.

LaTeX entrypoint: `latex.render_and_compile(master: MasterResume, tailored: TailoredResume | None) -> (tex: str, pdf_path: str, log: str)` — `tailored=None` renders the full master resume; rendered bullets carry `% grounded: <fact ids>` comments.

Database tables: `sessions(id, created_at)` · `master_resumes(id, session_id, data JSONB, updated_at)` · `applications(id, session_id, mode, jd_text NULL, jd_url TEXT NULL, status queued|running|done|failed, match_score, matched_keywords JSONB, missing_keywords JSONB, error, created_at)` · `resume_versions(id, application_id, tex TEXT, pdf_path, report JSONB, tailored JSONB NULL, created_at)`.

**Mock rule:** `core` ships `MOCK=1` (deterministic pass-through, no API key). Every other workflow builds against mock first, real later.

## Repo layout & conventions

```
emend/
├── core/    # Workflow A — schemas, prompts, pipeline, validators, evals (pure Python, zero web imports)
├── api/     # Workflow B — FastAPI, models, migrations, background jobs
├── latex/   # Workflow C — template, Jinja env, escaping, Tectonic wrapper
├── web/     # Workflow D — Next.js app + landing page
├── infra/   # Workflow C — Dockerfiles, compose, CI workflows
└── docs/    # this brief, the four workflow files, design components, demo persona fact file, architecture diagram
```

`main` intended to be protected (green CI + 1 review) — **not yet configured on GitHub as of this writing** (`branches/main/protection` 404s; anything can push straight to `main` today) · branches `feat/<area>/<slug>` / `fix/<area>/<slug>` · conventional commits · rotate reviewers across workflows · never edit another workflow's directories · if it's not in a workflow file, it doesn't exist — claim it before building it.

## Non-functional requirements

Warm compiles ~1–2s with a hard timeout · no network egress from the compile step at runtime · every rendered string passes the escaping filter · input size limits on all text fields · session-scoped access on every query and artifact · works cleanly on a phone (per the responsive spec) · fresh clone → one command → running app.

## Shared finish line

A stranger lands on **https://emend-two.vercel.app**, pastes their resume, confirms the facts, and gets it refactored into LaTeX — viewable both ways, copyable, downloadable, printable — then pastes a JD and gets a tailored version with a match score and grounding report, receipts visible in the `.tex`. The README carries the architecture diagram, usage GIF, and real eval numbers.

**Resume-honesty rule:** bullets go on our resumes when the thing they describe exists; bracketed numbers get filled in only once measured. Same rule the product enforces on itself.
