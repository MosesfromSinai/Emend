import { cn } from "@/lib/utils";

// The <ENTITY>-<NN> tag shown next to every fact — the same id that appears
// in the .tex `% grounded:` receipts, so a user can trace a bullet back here.
export function FactTag({ id, className }: { id: string; className?: string }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded bg-em-soft px-1.5 py-0.5 font-mono text-[11px] font-medium text-em-deep",
        className
      )}
    >
      {id}
    </span>
  );
}
