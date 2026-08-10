# Emend

**A tailored resume that can't lie about you.**

**[Try it live →](https://www.useemend.com)** — no sign-up, nothing saved until you confirm it.

Most resumes get filtered out by an ATS before a human ever reads them. Emend reverse-engineers that: it reads what a job posting actually prioritizes, then rewrites your resume to match — stronger verbs, quantified results, the right keywords — using only facts you confirmed about yourself.

You get real LaTeX out, not a locked-in template. Copy the `.tex`, download the PDF, keep both.

<!--
TODO: screenshots. Suggested shots, in order: (1) the landing hero, (2) the
Confirm screen (resume preview + fact list side by side), (3) the Tailor
screen with a live compatibility score and keyword chips, (4) the Export
screen's Resume/LaTeX toggle. Drop them in docs/screenshots/ and reference
with ![Confirm screen](docs/screenshots/confirm.png) etc.
-->

## How it works

**1. Paste your resume.** Emend breaks it into a list of atomic facts — one claim each, tagged with an id like `GA-01`.

**2. Confirm the facts.** You review the list and correct anything wrong. This screen is the whole product: everything downstream is locked to what you approved here.

**3. Refactor, or tailor.** With no job posting, you get a clean typeset version of what you confirmed. Paste a posting and you also get a match score, hit/miss keyword chips, and a rewritten resume aimed at that role.

**4. Take it with you.** Typeset PDF on one side, copyable `.tex` on the other.

## Why it can't make things up

Most AI resume tools will happily invent a metric that makes you look better. Emend is built so that it structurally can't.

- **The writer only sees confirmed facts.** It has no other input. It can select, merge, reword, and reorder them — it cannot add.
- **Every line carries a receipt.** Each generated bullet names the fact ids it came from, and those ids appear as comments in the `.tex` you download. You can trace any sentence back to something you approved.
- **Two checks before anything ships.** First a deterministic pass: every cited fact must exist, no bullet may be sourceless, and no number can appear that wasn't in the source facts. Then a second model audits each bullet against its sources and flags anything that overstates. A line that fails doesn't ship.
- **The match score is arithmetic, not opinion.** Keyword overlap is computed directly, so the number can't be flattered.
- **Gaps stay gaps.** If a posting wants something you haven't confirmed, Emend leaves it out rather than bridging it. A missing keyword is an honest result.

## Architecture

Four pieces, each doing one job:

- **web** — the landing page and the app: paste, confirm, and the side-by-side PDF / `.tex` workspace.
- **api** — sessions, storage, and the job runner. Tailoring takes a few seconds, so work happens in the background while the page polls for status.
- **core** — the pipeline: read the resume, read the posting, score the match, write the rewrite, validate it. This is where the no-invention rules live.
- **latex** — turns the approved facts into a real typeset document, stamping each bullet with its receipt, and compiles it in a locked-down sandbox.

No accounts. A session cookie holds your work, and every file is checked against that session before it's served.

---

Working on Emend? Local setup and deploys are in [infra/runbook.md](infra/runbook.md).
