# Workflow C — LaTeX Toolchain & Infra

**Owner: Teammate C** · Directories: `latex/` + `infra/` · Branches: `feat/latex/*`, `feat/infra/*`
**Hand-off:** paste `00-project-brief.md` + this file into Claude Cowork; build only inside `latex/` and `infra/`.

## Mission

Safely turn structured resume objects into beautiful PDFs and clean `.tex`, and own everything that runs the project — sandbox, dev environment, CI, and production. Both product views (rendered PDF and copyable LaTeX) are this workflow's output.

## Build list (implementation order)

1. The Jake's-style single-page LaTeX template; Jinja2 environment with `\VAR{}`/`\BLOCK{}` delimiters (defaults collide with LaTeX braces); escaping filter for `& % $ # _ { } ~ ^ \` applied to every rendered string. The output `.tex` must be clean enough that users are proud to copy it.
2. `latex.render_and_compile(master, tailored|None) -> (tex, pdf_path, log)` per the brief's Contracts: renders the master (refactor mode) or the tailored selection, compiles with Tectonic `--untrusted`, and surfaces compile logs on failure — never a silent hang.
3. Sandbox hardening in the api Docker image: pre-warmed package cache (~1–2s compiles, no network at runtime), hard timeout, CPU/memory caps, non-root user; hostile-input tests (shell-escape attempt, infinite loop, absurd length) must fail safely with a clean error.
4. docker-compose dev environment: web + api + postgres with hot reload; fresh clone → one command → working app.
5. CI (GitHub Actions per PR): ruff, pytest across `core`/`api`/`latex`, web build, api image build.
6. Deploys + secrets: Vercel (web), Fly.io or Railway (api + artifact volume), Neon (Postgres); a one-page runbook.

## Interfaces

**Exposes:** `latex.render_and_compile` (contract with Workflow B) and the running platform.
**Consumes:** `core` schemas.
**Do not:** enable shell-escape, allow network egress at compile time, or add queues/object storage.

## Acceptance criteria

Hostile `.tex` fails safely with a surfaced error · compiled output matches the template pixel-for-pixel on all four teammates' resumes · production URL live · one-command local dev from a fresh clone.

## Resume bullets earned

- Built a sandboxed LaTeX compilation service (Tectonic `--untrusted`, network-isolated image with pre-warmed cache, CPU/memory/time limits) rendering resumes in ~[X]s
- Designed the Jinja2→LaTeX rendering layer with custom delimiters and injection-safe escaping, producing user-facing `.tex` and print-ready PDFs
- Owned CI/CD and deployment for a 4-person product: per-PR GitHub Actions, one-command docker-compose dev env, production on Vercel + Fly.io with Neon Postgres
