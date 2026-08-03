import {
  DualViewVisual,
  GroundedRewriteVisual,
  MatchScoreVisual,
} from "@/components/landing/how-it-works-visuals";
import { Reveal } from "@/components/landing/reveal";

const STEPS = [
  {
    n: "01",
    kicker: "10-SECOND ANALYSIS",
    title: "Paste any job description.",
    body: "Copy a job posting and paste it in. Emend pulls out the keywords, skills, and experience the employer is scanning for — and scores your resume against them.",
    reverse: false,
  },
  {
    n: "02",
    kicker: "GROUNDED REWRITE",
    title: "Confirm your facts. We write from those — only those.",
    body: "Emend extracts every claim from your resume into facts you sign off on. The writer is structurally constrained to that list — every line it produces carries a reference to the fact it came from. Nothing invented, ever.",
    // the one alternating step: visual moves left, text moves right, per the
    // approved design (order:2/order:1 on the two columns)
    reverse: true,
  },
  {
    n: "03",
    kicker: "TYPESET & SHIP",
    title: "A real PDF and its LaTeX source, side by side.",
    body: "Download a professionally typeset PDF, or take the .tex source with you. Clean formatting that reads beautifully to both hiring systems and humans.",
    reverse: false,
  },
];

export function HowItWorks() {
  return (
    <div id="how" className="border-y border-em-softb bg-white">
      <div className="mx-auto max-w-270 px-8 py-19">
        <Reveal>
          <div className="mb-2.5 font-mono text-[11px] tracking-[.12em] text-em-accent">
            WORKFLOW
          </div>
          <h2 className="mb-2 text-[27px] font-semibold text-ink sm:text-[38px]">
            How it works.
          </h2>
          <p className="mb-13 text-base text-ink/70">
            From job posting to typeset resume in under a minute.
          </p>
        </Reveal>
        {STEPS.map((step) => (
          <Reveal
            key={step.n}
            className="mb-18 grid grid-cols-1 items-center gap-13 last:mb-0 md:grid-cols-2"
          >
            <div className={step.reverse ? "md:order-2" : undefined}>
              <div className="mb-1 font-serif text-[44px] font-semibold text-em-softb">
                {step.n}
              </div>
              <div className="mb-2 font-mono text-[11px] tracking-widest text-em-accent">
                {step.kicker}
              </div>
              <h3 className="mb-2.5 text-[21px] font-semibold text-ink sm:text-[26px]">
                {step.title}
              </h3>
              <p className="text-[14.5px] leading-relaxed text-ink/70">{step.body}</p>
            </div>
            <div className={step.reverse ? "md:order-1" : undefined}>
              <StepVisual n={step.n} />
            </div>
          </Reveal>
        ))}
      </div>
    </div>
  );
}

function StepVisual({ n }: { n: string }) {
  if (n === "01") return <MatchScoreVisual />;
  if (n === "02") return <GroundedRewriteVisual />;
  return <DualViewVisual />;
}
