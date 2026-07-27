# Emend · Workflow D — Web App, Landing Page & UX

**Owner: Teammate D** · Directory: `web/` · Branches: `feat/web/*`
**Hand-off:** paste `00-project-brief.md` + this file into Claude Cowork (plus `Emend Landing v2.dc.html` when building the landing); build only inside `web/`.

## Mission

Emend's face — the marketing landing page and the product itself, unified under the **Ink & Paper** brand. The money screen is the dual-view editor: rendered PDF beside clean, copyable LaTeX with its grounding receipts. The design bar is already set by the v2 landing component: paper, ink, amber, serif confidence.

## Build list (implementation order)

1. **Brand foundation:** Tailwind + shadcn theme mapped to the Ink & Paper tokens — paper `#faf8f4`, ink `#1c1b18`, amber family `#8a6d1f`/`#f3ecd9`/`#c9a648` exposed as `--em-accent|soft|softb|bright|deep` CSS vars (all new elements go through these vars so the four `colorScheme` options keep working); fonts: Source Serif 4 (headings), JetBrains Mono (fact tags, code, labels), system-ui (UI copy); dark code panes `#211f1a` with amber LaTeX highlighting.
2. **Landing page** — convert `Emend Landing v2.dc.html` into the Next.js app, preserving all sections: sticky blurred nav · hero (badge, product mock with JD-match card + blinking cursor, keyword chips, score ring, "grounded n/n" pill, floating fact-tag badges, CTA pair, trust line) · proof strip · how-it-works (3 alternating steps) · the **"Every sentence, your call"** demo (see item 3) · pipeline diagram + stat cards · FAQ accordion · CTA band · footer · scroll-reveal via IntersectionObserver honoring `revealMotion`/`revealReplay`.
   **Honesty guardrails from the brief's reconciliations:** hide/disable the "paste a link" field (URL ingestion deferred) · reword the "create a free account" CTA (no accounts in v1) · no invented testimonials — real quotes or drop the section · demo content stays grounded in `docs/demo-persona.md` (the Sam Reyes persona — reconciliation #5, decided) · stat cards show real measured numbers only.
3. **Interactive demo (scripted, client-side only):** floating "↓ try it — click any sentence below" hint pill · click a sentence → block highlight + dark toolbar · ‹ › cycles the three pre-written grounded rewrites (dots indicator), sourced from `docs/demo-persona.md` · "view my original" reverts to original wording, "↩ back to my edit / Emend's rewrite" returns · **click-to-edit for real:** typing shows "↺ discard my edit" instantly; blur/Enter saves the edit (tag flips to "edited ✎", label "your edit · based on fact HX-01"); cycling or discard replaces it · click off deselects · every bullet shows its fact tag, flipping to "original" on revert. **Implementation notes from the design component:** sentence state updates use functional setState (stale-closure race fix); the contenteditable span carries a state-derived `key` so text remounts when its source changes.
4. **Responsive:** translate the design component's `.em-*` media-query classes into Tailwind responsive utilities, preserving behavior — **≤960px:** hero & workflow steps → 1 column (text first), pipeline stacks with rotated arrows, testimonials stack, footer 2-col; **≤680px:** smaller headings, nav anchors hidden (logo + Get started stay), tighter padding, resume card slims, stats/CTA/step-3 rows stack, floating hero badges hidden, footer 1-col; no horizontal overflow anywhere.
5. App shell + handwritten API types matching Workflow B's OpenAPI spec; build against `core`'s `MOCK=1` shapes first so nothing blocks on the backend.
6. Onboarding: paste resume text → render the proposed facts with their `GA-01`-style tags → user edits/confirms each → save. Confirmation is where the grounding guarantee starts.
7. Dual-view workspace: react-pdf pane + dark monospace `.tex` pane (grounding comments visible) with a copy button; **Download PDF** / **Download .tex**; print-friendly.
8. Refactor flow: one obvious "Refactor my resume" button from confirmation straight into the dual view — no JD required.
9. Tailor flow: JD paste box → match-score ring + hit/miss keyword chips + "grounded n/n" pill (from `Report`) → tailored dual view → read-only provenance panel showing each bullet's source facts.
10. Async job UX: submit → pending → poll `GET /applications/{id}` → success/failure screens with surfaced compile logs; history list with re-open/re-download; designed empty/loading/error states; record the README demo GIF.

## Interfaces

**Exposes:** the deployed UI and landing page.
**Consumes:** Workflow B's REST API only; the fact-id scheme and `Report` shape from the Contracts.
**Do not:** call the LLM or database directly, add auth screens, build **live** per-sentence rewrite cycling in the workspace (the landing demo is scripted; live cycling is post-MVP), or introduce colors outside the `--em-*` vars.

## Acceptance criteria

A first-time visitor lands on the Emend page and gets to copied `.tex` and a downloaded PDF with zero instructions · the landing matches the v2 design component, including the full demo interaction set and both breakpoints (≤960px, ≤680px), with all four color schemes working · both workspace views render correctly on a phone · every async state has a designed screen · no invented content anywhere on the site.

## Resume bullets earned

- Shipped the marketing site and product frontend for Emend, an LLM resume platform (Next.js, TypeScript, Tailwind/shadcn): a themeable design-token brand system, fact-confirmation onboarding, and a dual-view LaTeX editor (live PDF preview + copyable `.tex`)
- Implemented async job UX — submission, status polling, failure recovery with surfaced compile diagnostics — against a FastAPI backend
- Built the interactive grounded-rewrite landing demo (stateful per-sentence editing, rewrite cycling, provenance tags) and workspace visualizations surfacing the system's no-invented-claims guarantee

## Stretch

Live per-sentence rewrite cycling in the workspace (the landing demo's interaction, made real), dark mode, shareable read-only links, Lighthouse ≥ 90.
