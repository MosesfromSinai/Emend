// The score is a read on fit, not a target to write toward -- Emend never
// inserts a keyword the candidate doesn't have, so the label describes how
// much of the posting the confirmed facts already cover, not a grade.
function compatibilityLabel(missingCount: number): string {
  if (missingCount === 0) return "Strongly compatible";
  return `Compatible, with ${missingCount} real gap${missingCount === 1 ? "" : "s"}`;
}

// conic-gradient ring matching the design component's JD-match card.
export function MatchScoreRing({
  score,
  missingCount,
}: {
  score: number;
  missingCount: number;
}) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-full"
          style={{
            background: `conic-gradient(var(--em-accent) 0 ${pct}%, var(--em-softb) ${pct}% 100%)`,
          }}
        >
          <div className="flex h-6.5 w-6.5 items-center justify-center rounded-full bg-white text-[11px] font-bold text-ink">
            {pct}
          </div>
        </div>
        <span className="text-sm font-semibold text-ink">
          {compatibilityLabel(missingCount)}
        </span>
      </div>
      <p className="text-xs text-ink/60">
        How well your confirmed facts already line up with this posting.
      </p>
    </div>
  );
}
