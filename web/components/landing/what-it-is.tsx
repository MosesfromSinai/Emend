import { Reveal } from "@/components/landing/reveal";
import { PipelineDiagram } from "@/components/landing/pipeline-diagram";

// Stat cards are claims true by construction, not usage metrics — the brief
// requires "real measured numbers only" and this is a pre-launch product
// with no users yet. 12/12 is the shipped demo's own sentence count; .tex
// describes the deliverable; the match-score claim is a fact about the
// architecture (core/matching.py never calls the LLM), not a benchmark.
const STATS = [
  { value: "12/12", label: "demo lines grounded in confirmed facts, above" },
  { value: ".tex", label: "full LaTeX source — your resume is yours" },
  { value: "0", label: "LLM calls in your match score — pure keyword math" },
];

export function WhatItIs() {
  return (
    <div id="what" className="border-y border-em-softb bg-white">
      <div className="mx-auto max-w-[840px] px-8 py-19">
        <Reveal>
          <div className="mb-2.5 font-mono text-[11px] tracking-[.12em] text-em-accent">
            ABOUT
          </div>
          <h2 className="mb-2 text-[27px] font-semibold text-ink sm:text-[38px]">
            Structured, so it can&apos;t hallucinate.
          </h2>
          <p className="mb-7 text-base text-ink/70">
            The resume tool built for how hiring actually works — without
            lying for you.
          </p>
        </Reveal>

        <Reveal>
          <PipelineDiagram />
        </Reveal>

        <Reveal className="flex flex-col gap-4.5 text-[15.5px] leading-loose text-[#3a372f]">
          <p>
            Most resumes are rejected before a human reads them. Hiring
            systems scan, filter, and rank candidates on keyword matches and
            formatting patterns. If your resume doesn&apos;t speak that
            language, it&apos;s filtered out — regardless of what you&apos;ve
            actually done.
          </p>
          <p>
            Emend reverse-engineers that process. Paste a job description and
            it extracts what the employer is prioritizing, then rewrites your
            resume to match — stronger verbs, quantified results, the right
            framing.
          </p>
          <p>
            <strong className="font-semibold text-ink">
              The difference: Emend can&apos;t make things up.
            </strong>{" "}
            Other AI resume tools generate free-form text and hope it&apos;s
            true. Emend&apos;s pipeline is structured — the writer literally
            has no input except the facts you confirmed, and every output
            line is tagged with the fact it was built from. If a line has no
            source, it doesn&apos;t ship.
          </p>
        </Reveal>

        <Reveal className="mt-8 flex flex-col gap-3 sm:flex-row">
          {STATS.map((stat) => (
            <div
              key={stat.value}
              className="flex-1 rounded-[10px] border border-em-softb bg-paper px-5 py-4.5"
            >
              <div className="font-serif text-2xl font-bold text-ink">{stat.value}</div>
              <div className="text-[12.5px] text-ink/70">{stat.label}</div>
            </div>
          ))}
        </Reveal>
      </div>
    </div>
  );
}
