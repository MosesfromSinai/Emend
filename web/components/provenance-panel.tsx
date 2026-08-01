import { FactTag } from "@/components/ui/fact-tag";
import type { BulletVerdict } from "@/lib/types";

// Read-only: "each bullet's source facts" per the brief's tailor-flow item.
// Reads BulletVerdict.source_fact_ids directly from the Report — no need to
// parse `% grounded:` comments out of the tex.
export function ProvenancePanel({ verdicts }: { verdicts: BulletVerdict[] }) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="font-serif text-lg font-semibold">Grounding report</h3>
      <ul className="flex flex-col gap-2">
        {verdicts.map((verdict, index) => (
          <li
            key={index}
            className={
              "rounded-md border p-3 text-sm " +
              (verdict.supported
                ? "border-em-softb bg-white"
                : "border-red-300 bg-red-50")
            }
          >
            <div className="mb-1 flex flex-wrap items-center gap-1.5">
              {verdict.source_fact_ids.map((id) => (
                <FactTag key={id} id={id} />
              ))}
              <span className={verdict.supported ? "text-[#5a6a34]" : "text-red-700"}>
                {verdict.supported ? "✓ supported" : "⚠ unsupported"}
              </span>
            </div>
            <p className="text-ink">{verdict.bullet}</p>
            <p className="mt-1 text-xs text-ink/60">{verdict.reason}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
