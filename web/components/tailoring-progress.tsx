"use client";

import { useEffect, useState } from "react";

// The backend gives us queued/running, not a real percentage -- ticking a
// bar that eases toward (but never reaches) 92% reads as "still working"
// instead of the spinner alone, without lying that we know exactly how
// close it is. The caller jumps it to 100%/removes it once the real work
// is done. `timeConstantMs` is the one thing that varies by caller: a full
// tailor run can take up to a minute, while the JD score card is normally
// sub-second (no LLM call, just local keyword matching) and only ever
// slow when the user pasted a URL that's fetching -- a bar tuned for a
// minute-long wait would barely move before that one's already done.
const ASYMPTOTE = 92;
const TICK_MS = 200;

export function AsymptoticProgress({
  timeConstantMs,
  caption,
}: {
  timeConstantMs: number;
  caption?: string;
}) {
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => setElapsedMs(Date.now() - start), TICK_MS);
    return () => clearInterval(timer);
  }, []);

  const percent = ASYMPTOTE * (1 - Math.exp(-elapsedMs / timeConstantMs));

  return (
    <div className="flex w-full max-w-xs flex-col gap-1.5">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-em-softb">
        <div
          className="h-full rounded-full bg-em-accent transition-[width] duration-200 ease-linear"
          style={{ width: `${percent}%` }}
        />
      </div>
      {caption && <p className="text-xs text-ink/50">{caption}</p>}
    </div>
  );
}

export function TailoringProgress({ mode }: { mode: "tailor" | "refactor" }) {
  return (
    <AsymptoticProgress
      timeConstantMs={18_000}
      caption={
        mode === "tailor"
          ? "Every line gets checked against your confirmed facts before it ships, so this can take up to a minute."
          : undefined
      }
    />
  );
}
