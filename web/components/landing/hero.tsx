import Link from "next/link";

import { HeroMock } from "@/components/landing/hero-mock";
import { Reveal } from "@/components/landing/reveal";

export function Hero() {
  return (
    <div className="mx-auto grid max-w-[1080px] grid-cols-1 gap-14 px-8 py-19 md:grid-cols-2 md:items-center md:py-22">
      <Reveal>
        <div className="mb-5 inline-flex items-center gap-1.5 rounded-full border border-em-softb bg-em-soft px-3.5 py-1.5 font-mono text-[11px] text-em-accent">
          structured generation · no hallucination by design
        </div>
        <h1 className="mb-4 text-[34px] leading-[1.1] font-semibold text-ink sm:text-[52px] sm:leading-[1.08]">
          A tailored resume that can&apos;t lie about you.
        </h1>
        <p className="mb-7 max-w-md text-[17px] leading-relaxed text-ink/70">
          Paste a job description. Emend rewrites your resume around it —
          constrained to facts you confirm, typeset in LaTeX, with a receipt
          for every line.
        </p>
        <div className="mb-5 flex flex-wrap items-center gap-3">
          <Link
            href="/app/workspace"
            className="rounded-lg bg-ink px-6.5 py-3.5 text-[15px] font-semibold text-paper shadow-[0_2px_8px_rgba(28,27,24,.18)] hover:bg-em-deep"
          >
            Tailor my resume →
          </Link>
          <Link
            href="/app"
            className="rounded-lg border-[1.5px] border-[#d8d1c2] bg-white px-5.5 py-3 text-[15px] font-semibold text-ink hover:border-ink"
          >
            Upload existing resume
          </Link>
        </div>
        <div className="flex flex-wrap gap-x-4.5 gap-y-2.5 text-xs font-medium text-[#8f8874]">
          <span>✓ JD keyword matching</span>
          <span>✓ LaTeX-quality PDF</span>
          <span>✓ Nothing made up</span>
        </div>
      </Reveal>
      <Reveal delayMs={150}>
        <HeroMock />
      </Reveal>
    </div>
  );
}
