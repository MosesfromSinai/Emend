# Workflow D — Web App & UX

**Owner: Teammate D** · Directory: `web/` · Branches: `feat/web/*`
**Hand-off:** paste `00-project-brief.md` + this file into Claude Cowork; build only inside `web/`.

## Mission

The product's face. The money screen is the dual-view editor — the user's refactored resume as a rendered PDF beside clean, copyable LaTeX. The bar is the reference site (resutex.com): clean, fast, obvious. If the demo GIF makes people want to try it, this workflow did its job.

## Build list (implementation order)

1. Next.js App Router shell (TypeScript, Tailwind + shadcn/ui); handwritten API types matching Workflow B's OpenAPI spec; build against `core`'s `MOCK=1` shapes first so nothing blocks on the backend.
2. Onboarding: paste resume text → render the proposed facts → user edits/confirms each → save. Treat confirmation as a product feature — it's where the grounding guarantee starts.
3. Dual-view workspace: react-pdf pane + monospace `.tex` pane with a copy button; **Download PDF** and **Download .tex**; print-friendly.
4. Refactor flow: one obvious "Refactor my resume" button from confirmation straight into the dual view — no JD required.
5. Tailor flow: JD paste box → match score + hit/miss keyword chips → tailored dual view → read-only grounding/provenance panel showing each bullet's source facts.
6. Async job UX: submit → pending → poll `GET /applications/{id}` → success/failure screens with surfaced compile logs.
7. History list with re-open/re-download; responsive layout; designed empty/loading/error states everywhere; record the README demo GIF.

## Interfaces

**Exposes:** the deployed UI.
**Consumes:** Workflow B's REST API only.
**Do not:** call the LLM or the database directly, add auth screens, or build accept/reject editing.

## Acceptance criteria

A first-time visitor gets from landing to copied `.tex` and a downloaded PDF with zero instructions · both views render correctly on a phone · every async state has a designed screen.

## Resume bullets earned

- Shipped the product frontend (Next.js, TypeScript, Tailwind/shadcn) for an LLM resume platform: fact-confirmation onboarding and a dual-view LaTeX editor (live PDF preview + copyable `.tex` source)
- Implemented async job UX — submission, status polling, failure recovery with surfaced compile diagnostics — against a FastAPI backend
- Built match-score visualization and a source-fact provenance panel surfacing the system's no-invented-claims guarantee on a deployed 4-person product
