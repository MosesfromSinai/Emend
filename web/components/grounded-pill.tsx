export function GroundedPill({
  supportedCount,
  total,
}: {
  supportedCount: number;
  total: number;
}) {
  const allGrounded = supportedCount === total;
  return (
    <span
      className={
        "rounded-full px-3 py-1 font-mono text-xs font-semibold " +
        (allGrounded ? "bg-em-ok-bg text-em-ok-fg" : "bg-em-warn-bg text-em-warn-fg")
      }
    >
      {allGrounded ? "✓" : "⚠"} grounded {supportedCount}/{total}
    </span>
  );
}
