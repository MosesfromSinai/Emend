export function HeroMock() {
  return (
    <div className="relative">
      <div className="overflow-hidden rounded-xl border border-em-softb bg-white shadow-[0_8px_32px_rgba(28,27,24,.1)]">
        <div className="flex items-center justify-between border-b border-em-softb bg-[#f4f0e6] px-4 py-2.5">
          <span className="font-serif text-xs font-semibold text-ink">
            Emend — JD Match
          </span>
          <span className="flex gap-1.5">
            {[0, 1, 2].map((i) => (
              <span key={i} className="h-2 w-2 rounded-full bg-[#ddd5c2]" />
            ))}
          </span>
        </div>
        <div className="px-5.5 py-5">
          <div className="mb-1.5 font-mono text-[10.5px] font-semibold tracking-wide text-[#9a927f]">
            JOB DESCRIPTION
          </div>
          <div className="rounded-lg border border-em-softb bg-paper px-3.5 py-3 font-mono text-xs leading-relaxed text-ink/70">
            &quot;New-grad SWE. Python, React, CI/CD, AWS, distributed systems…&quot;
            <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-em-accent align-text-bottom" />
          </div>
          {/* job-URL ingestion is deferred (brief reconciliation #1) */}
          <div
            title="Coming soon"
            className="mt-2 flex cursor-not-allowed items-center gap-2 rounded-lg border-[1.5px] border-dashed border-[#ddd5c2] bg-white px-3.5 py-2.5 opacity-60"
          >
            <span className="text-xs text-[#9a927f]">
              Paste a link to the posting — coming soon
            </span>
          </div>
          <div className="my-3.5 flex flex-wrap gap-1.5 font-mono text-[11px]">
            {["python", "react", "ci/cd", "aws"].map((kw) => (
              <span key={kw} className="rounded bg-[#eef0e2] px-2 py-1 text-[#5a6a34]">
                {kw} ✓
              </span>
            ))}
            <span className="rounded bg-[#f4e6e2] px-2 py-1 text-[#9a4a34]">
              distributed systems
            </span>
          </div>
          <div className="flex items-center justify-between border-t border-[#efe9dc] pt-3.5">
            <div className="flex items-center gap-2">
              <div
                className="flex h-[38px] w-[38px] items-center justify-center rounded-full"
                style={{
                  background:
                    "conic-gradient(var(--em-accent) 0 82%, #efe9dc 82% 100%)",
                }}
              >
                <div className="flex h-[29px] w-[29px] items-center justify-center rounded-full bg-white text-xs font-bold text-ink">
                  82
                </div>
              </div>
              <div>
                <div className="text-[12.5px] font-semibold text-ink">Strong match</div>
                <div className="text-[11px] text-[#9a927f]">1 keyword to address</div>
              </div>
            </div>
            <span className="rounded-full bg-[#eef0e2] px-3 py-1 text-[11px] font-semibold text-[#5a6a34]">
              ✓ grounded 12/12
            </span>
          </div>
        </div>
      </div>
      <div className="absolute -top-4 -right-3.5 hidden animate-bounce rounded-lg bg-[#211f1a] px-3 py-2 font-mono text-[10.5px] whitespace-nowrap text-[#c9c4b6] shadow-lg sm:block">
        <span className="text-[#8f887a]">% grounded:</span>{" "}
        <span className="text-em-bright">fact HX-02</span>
      </div>
      <div className="absolute -bottom-3.5 -left-4.5 hidden rounded-lg border border-em-softb bg-white px-3 py-2 text-[11px] font-semibold text-[#5a6a34] shadow-md sm:block">
        ✓ every line has a source
      </div>
    </div>
  );
}
