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
        (allGrounded ? "bg-[#eef0e2] text-[#5a6a34]" : "bg-[#f4e6e2] text-[#9a4a34]")
      }
    >
      {allGrounded ? "✓" : "⚠"} grounded {supportedCount}/{total}
    </span>
  );
}
