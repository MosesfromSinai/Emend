"use client";

import { useEffect, useState } from "react";

// The backend gives us queued/running, not a real percentage -- ticking a
// bar that eases toward (but never reaches) 92% reads as "still working"
// instead of the spinner alone, without lying that we know exactly how
// close it is. It jumps to 100% only when the caller's status goes terminal.
const ASYMPTOTE = 92;
const TIME_CONSTANT_MS = 18_000;
const TICK_MS = 200;

export function TailoringProgress({ mode }: { mode: "tailor" | "refactor" }) {
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => setElapsedMs(Date.now() - start), TICK_MS);
    return () => clearInterval(timer);
  }, []);

  const percent = ASYMPTOTE * (1 - Math.exp(-elapsedMs / TIME_CONSTANT_MS));

  return (
    <div className="flex w-full max-w-xs flex-col gap-1.5">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-em-softb">
        <div
          className="h-full rounded-full bg-em-accent transition-[width] duration-200 ease-linear"
          style={{ width: `${percent}%` }}
        />
      </div>
      {mode === "tailor" && (
        <p className="text-xs text-ink/50">
          Every line gets checked against your confirmed facts before it ships,
          so this can take up to a minute.
        </p>
      )}
    </div>
  );
}
