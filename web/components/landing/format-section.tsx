import Link from "next/link";

import { PERSONA_NAME } from "@/lib/demo-persona";
import { Reveal } from "@/components/landing/reveal";

const BENEFITS: { lead: string; rest: string }[] = [
  {
    lead: "Rewriting is opt-in.",
    rest: "Nothing changes unless you ask. No match score, no posting, no surprises.",
  },
  {
    lead: "Consistent everything.",
    rest: "Margins, dates, bullet spacing, and section rules all line up on their own.",
  },
  {
    lead: "Polish it with AI, or edit it yourself.",
    rest: "Ask for a professional rewrite of the whole resume whenever you want, or click any line and write it in your own words. Still grounded in what you confirmed.",
  },
  {
    lead: "Yours to keep.",
    rest: "Download the PDF and the .tex source together.",
  },
];

export function FormatSection() {
  return (
    <div id="polish" className="border-y border-em-softb bg-white">
      <div className="mx-auto grid max-w-270 grid-cols-1 items-center gap-13 px-8 py-19 md:grid-cols-2">
        <Reveal>
          <div className="mb-2.5 font-mono text-[11px] tracking-[.12em] text-em-accent">
            NO POSTING NEEDED
          </div>
          <h2 className="mb-3 text-[27px] font-semibold text-ink sm:text-[38px]">
            Not job hunting? Just make it beautiful.
          </h2>
          <p className="mb-6 text-[15px] leading-relaxed text-ink/70">
            Plenty of people don&apos;t need tailoring. They have a resume
            that says the right things and looks like a Word document from
            2011. Skip the job description entirely and Emend will format
            exactly what you wrote, word for word, in real LaTeX. Then, if
            you want, ask us to rewrite the whole thing to read more
            professionally.
          </p>
          <ul className="mb-7 flex flex-col gap-3">
            {BENEFITS.map((b) => (
              <li key={b.lead} className="flex items-start gap-2.5">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-em-ok-bg text-[11px] font-bold text-em-ok-fg">
                  ✓
                </span>
                <span className="text-[14.5px] leading-relaxed text-ink/70">
                  <strong className="font-semibold text-ink">{b.lead}</strong> {b.rest}
                </span>
              </li>
            ))}
          </ul>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/app"
              className="rounded-lg bg-em-accent px-6.5 py-3.5 text-[15px] font-semibold text-paper shadow-[0_2px_10px_rgba(138,58,48,.35)] hover:bg-em-deep hover:shadow-[0_4px_14px_rgba(138,58,48,.45)]"
            >
              Just format my resume
            </Link>
            <span className="text-xs text-ink/50">
              Takes about a minute. No posting required.
            </span>
          </div>
        </Reveal>

        <Reveal>
          <FormatBeforeAfter />
        </Reveal>
      </div>
    </div>
  );
}

// Same real content on both sides -- the whole argument of this section is
// that only presentation differs, never the words. Sam Reyes / Helix
// Dynamics is the app's one fictional demo persona (lib/demo-persona.ts),
// reused here rather than inventing new placeholder content.
function FormatBeforeAfter() {
  return (
    <div className="overflow-hidden rounded-xl border border-em-softb bg-white shadow-[0_8px_32px_rgba(28,27,24,.1)]">
      <div className="flex items-center justify-between border-b border-em-softb bg-[#f4f0e6] px-4 py-2.5">
        <span className="font-mono text-[11px] font-semibold tracking-wide text-em-ink-2">
          FORMAT AS-IS
        </span>
        <span className="rounded-full bg-em-ok-bg px-2.5 py-1 text-[10.5px] font-semibold text-em-ok-fg">
          rewrites on request
        </span>
      </div>

      <div className="grid grid-cols-2 divide-x divide-em-softb">
        <div className="flex flex-col bg-paper p-4">
          <div className="mb-2.5 font-mono text-[9px] font-semibold tracking-wide text-em-faint">
            WHAT YOU UPLOAD
          </div>
          <MessyMiniResume />
          <p className="mt-2.5 text-[10px] text-ink/45">
            inconsistent dashes, ragged dates
          </p>
        </div>
        <div className="flex flex-col bg-[#f4f0e6] p-4">
          <div className="mb-2.5 font-mono text-[9px] font-semibold tracking-wide text-em-accent">
            WHAT YOU DOWNLOAD
          </div>
          <div className="bg-white p-3 shadow-[0_2px_10px_rgba(28,27,24,.12)]">
            <CleanMiniResume />
          </div>
          <p className="mt-2.5 text-[10px] text-em-accent">
            same words, properly formatted
          </p>
        </div>
      </div>

      <div className="border-t border-em-softb bg-paper px-4 py-2.5 text-center text-[11px] text-ink/60">
        Nothing here was rewritten. Ask us to polish a line and only that
        line changes.
      </div>
    </div>
  );
}

function MessyMiniResume() {
  return (
    <div className="font-sans text-[#333]">
      <div className="text-[7px] font-bold">{PERSONA_NAME}</div>
      <div className="text-[4.5px] text-[#666]">
        sam.reyes@example.com, linkedin.com/in/samreyes-demo
      </div>
      <div className="mt-1.5 text-[5px] font-bold">Experience</div>
      <div className="text-[4.5px] leading-tight">
        Software Engineer Intern - Helix Dynamics - San Diego, CA - Jun
        2026-Present
      </div>
      <div className="text-[4.5px] leading-tight text-[#444]">
        - Developed 20+ Python integration tests validating message flow
        across 5 microservices
        <br />- Automated dev-environment setup into one-command scripts,
        cutting setup to under 10 minutes
      </div>
      <div className="mt-1.5 text-[5px] font-bold">Projects</div>
      <div className="text-[4.5px] leading-tight">
        TrailScout - Python, YOLOv8, Jetson Nano
      </div>
      <div className="text-[4.5px] leading-tight text-[#444]">
        - Deployed real-time wildlife detection at the edge with a live
        dashboard
      </div>
    </div>
  );
}

function CleanMiniResume() {
  return (
    <div>
      <div className="text-center font-serif text-[7px] font-bold text-[#111]">
        {PERSONA_NAME}
      </div>
      <div className="mt-0.5 mb-1.5 text-center font-mono text-[4.5px] text-[#555]">
        sam.reyes@example.com · linkedin.com/in/samreyes-demo
      </div>
      <div className="mb-1 border-b border-[#111] pb-0.5 font-serif text-[5.5px] font-bold text-[#111]">
        EXPERIENCE
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-[5px] font-semibold text-[#222]">
          Software Engineer Intern
        </span>
        <span className="text-[4.5px] text-[#555]">Jun 2026 – Present</span>
      </div>
      <div className="text-[4.5px] italic text-[#555]">
        Helix Dynamics — San Diego, CA
      </div>
      <div className="ml-1 mt-0.5 text-[4.5px] leading-relaxed text-[#444]">
        • Developed 20+ Python integration tests validating message flow
        across 5 microservices
        <br />• Automated dev-environment setup into one-command scripts,
        cutting setup to under 10 minutes
      </div>
      <div className="mt-1 mb-1 border-b border-[#111] pb-0.5 font-serif text-[5.5px] font-bold text-[#111]">
        PROJECTS
      </div>
      <div className="text-[5px] font-semibold text-[#222]">TrailScout</div>
      <div className="text-[4.5px] italic text-[#555]">
        Python · YOLOv8 · Jetson Nano
      </div>
      <div className="ml-1 mt-0.5 text-[4.5px] leading-relaxed text-[#444]">
        • Deployed real-time wildlife detection at the edge with a live
        dashboard
      </div>
    </div>
  );
}
