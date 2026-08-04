import { PERSONA_NAME } from "@/lib/demo-persona";

export function GroundedRewriteVisual() {
  return (
    <div className="rounded-xl border border-em-softb bg-paper p-5.5">
      <div className="mb-2 flex items-start gap-2.5 rounded-lg border border-em-softb bg-white px-3.5 py-2.5">
        <span className="font-semibold text-[#7a8a4a]">✓</span>
        <div>
          <div className="mb-0.5 text-[10px] font-semibold tracking-wide text-[#9a927f]">
            FACT HX-02 · CONFIRMED BY YOU
          </div>
          <div className="text-[12.5px] text-[#3a372f]">
            Multi-step dev setup → one-command Bash scripts · −80% setup time
          </div>
        </div>
      </div>
      <div className="my-2 text-center text-xs font-medium text-em-accent">
        ↓ becomes
      </div>
      <div className="rounded-lg bg-code-pane px-4 py-3.5 font-mono text-[11.5px] leading-relaxed text-[#c9c4b6]">
        <div className="text-[#8f887a]">% grounded: fact HX-02</div>
        <div>
          <span className="text-em-bright">\resumeItem</span>
          {"{Automated a multi-step dev environment"}
        </div>
        <div>&nbsp;&nbsp;setup into one-command Bash scripts, cutting</div>
        <div>
          &nbsp;&nbsp;setup time by <span className="text-[#e0d7bd]">80\%</span>
          {"}"}
        </div>
      </div>
    </div>
  );
}

export function MatchScoreVisual() {
  return (
    <div className="rounded-xl border border-em-softb bg-paper p-5.5">
      <div className="mb-2 font-mono text-[10.5px] font-semibold tracking-wide text-[#9a927f]">
        JOB DESCRIPTION
      </div>
      <div className="mb-2 rounded-lg border border-em-softb bg-white px-3.5 py-3 font-mono text-xs text-[#3a372f]">
        &quot;New-grad software engineer with Python, React, CI/CD pipelines,
        AWS…&quot;
      </div>
      <div className="mb-3.5 rounded-lg border-[1.5px] border-dashed border-em-softb bg-white px-3.5 py-2.5">
        <span className="text-xs text-[#9a927f]">
          Have a link to the posting? Paste it here instead
        </span>
      </div>
      <div className="mb-3.5 flex flex-wrap gap-1.5 font-mono text-[11px]">
        {["Python", "React", "CI/CD", "AWS", "Docker"].map((kw) => (
          <span key={kw} className="rounded bg-em-soft px-2 py-1 text-em-deep">
            {kw}
          </span>
        ))}
      </div>
      <div className="flex items-center justify-between border-t border-[#efe9dc] pt-3">
        <span className="text-[12.5px] font-semibold text-ink">Match score</span>
        <div className="ml-4 flex flex-1 items-center gap-2.5">
          <div className="h-1.75 flex-1 overflow-hidden rounded bg-[#efe9dc]">
            <div className="h-full w-[82%] rounded bg-em-accent" />
          </div>
          <span className="font-serif text-sm font-bold text-em-accent">82%</span>
        </div>
      </div>
    </div>
  );
}

export function DualViewVisual() {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-em-softb bg-paper p-5.5 sm:flex-row">
      <div className="flex-1 bg-white p-4 shadow-[0_2px_10px_rgba(28,27,24,.12)]">
        <div className="text-center font-serif text-[10px] font-bold text-[#111]">
          {PERSONA_NAME}
        </div>
        <div className="mt-0.5 mb-2 text-center font-mono text-[4.5px] text-[#555]">
          sam.reyes@example.com · linkedin.com/in/samreyes-demo
        </div>
        <div className="mb-1 border-b border-[#111] pb-0.5 font-serif text-[5.5px] font-bold text-[#111]">
          EXPERIENCE
        </div>
        <div className="text-[5px] font-semibold text-[#222]">
          Software Engineer Intern — Helix Dynamics
        </div>
        <div className="ml-1 text-[4.5px] leading-relaxed text-[#444]">
          • 20+ integration tests across 5 microservices
          <br />• One-command Bash setup, −80% setup time
        </div>
        <div className="mt-1 mb-1 border-b border-[#111] pb-0.5 font-serif text-[5.5px] font-bold text-[#111]">
          PROJECTS
        </div>
        <div className="text-[5px] font-semibold text-[#222]">
          LayoverLog — Flask, PostgreSQL, Docker
        </div>
        <div className="ml-1 text-[4.5px] leading-relaxed text-[#444]">
          • Flask + PostgreSQL app on a normalized 5-table schema
        </div>
      </div>
      <div className="flex flex-1 flex-col justify-center gap-2.5">
        {["PDF ready", ".tex source included", "Passes major ATS systems"].map(
          (label) => (
            <div key={label} className="flex items-center gap-2 text-xs font-semibold text-ink">
              <span className="flex h-5.5 w-5.5 items-center justify-center rounded-full bg-[#eef0e2] text-[12px] text-[#5a6a34]">
                ✓
              </span>
              {label}
            </div>
          )
        )}
      </div>
    </div>
  );
}
