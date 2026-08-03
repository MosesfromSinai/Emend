import { Reveal } from "@/components/landing/reveal";

// The design's proof strip shows usage stats ("1,200+ resumes tailored",
// "82% avg. match") — this is a pre-launch product with no users yet, so
// those would be fabricated. Same rule the product enforces on generated
// bullets applies to its own marketing: claims true by construction only,
// nothing that needs usage data we don't have.
const STATS = [
  { value: "0", label: "invented claims — by design" },
  { value: "2", label: "independent checks before any bullet ships" },
  { value: "100%", label: "of bullets carry a confirmed fact citation" },
  { value: "< 60s", label: "posting → typeset PDF" },
];

export function ProofStrip() {
  return (
    <div className="border-t border-em-softb">
      <Reveal className="mx-auto flex max-w-270 flex-wrap items-baseline justify-center gap-x-14 gap-y-3.5 px-8 py-6.5">
        {STATS.map((stat) => (
          <div key={stat.label} className="flex items-baseline gap-2">
            <span className="font-serif text-2xl font-bold text-ink">{stat.value}</span>
            <span className="text-[13px] text-ink/60">{stat.label}</span>
          </div>
        ))}
      </Reveal>
    </div>
  );
}
