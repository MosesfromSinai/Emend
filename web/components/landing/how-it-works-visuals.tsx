import { PERSONA_NAME } from "@/lib/demo-persona";

export function MatchScoreVisual() {
  return (
    <div className="rounded-xl border border-em-softb bg-paper p-5.5">
      <div className="mb-2 font-mono text-[10.5px] font-semibold tracking-wide text-[#9a927f]">
        JOB DESCRIPTION
      </div>
      <div className="mb-3 rounded-lg border border-em-softb bg-white px-3.5 py-3 font-mono text-xs text-[#3a372f]">
        &quot;New-grad software engineer with Python, React, CI/CD pipelines,
        AWS…&quot;
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
          <div className="h-[7px] flex-1 overflow-hidden rounded bg-[#efe9dc]">
            <div className="h-full w-[82%] rounded bg-em-accent" />
          </div>
          <span className="font-serif text-sm font-bold text-em-accent">82%</span>
        </div>
      </div>
    </div>
  );
}
