const STEPS = [
  {
    n: "STEP 1",
    title: "Your resume",
    body: "Plain text in, exactly as you wrote it.",
    highlight: false,
  },
  {
    n: "STEP 2",
    title: "Facts you confirm",
    body: "Every claim becomes a numbered fact you sign off on.",
    highlight: false,
  },
  {
    n: "STEP 3",
    title: "Constrained writer",
    body: "The AI can only compose from your fact list — structurally.",
    highlight: true,
  },
  {
    n: "STEP 4",
    title: "Grounding report",
    body: "Every line → its source fact. Auditable receipts.",
    highlight: false,
  },
];

export function PipelineDiagram() {
  return (
    <div className="mb-8.5 grid grid-cols-1 items-stretch gap-2.5 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr]">
      {STEPS.map((step, i) => (
        <PipelineStepFragment key={step.n} step={step} isLast={i === STEPS.length - 1} />
      ))}
    </div>
  );
}

function PipelineStepFragment({
  step,
  isLast,
}: {
  step: (typeof STEPS)[number];
  isLast: boolean;
}) {
  return (
    <>
      <div
        className={
          step.highlight
            ? "rounded-[10px] border border-em-softb bg-em-soft px-3.75 py-3.5"
            : "rounded-[10px] border border-em-softb bg-paper px-3.75 py-3.5"
        }
      >
        <div
          className={
            "mb-1.25 font-mono text-[10px] font-semibold " +
            (step.highlight ? "text-em-accent" : "text-[#9a927f]")
          }
        >
          {step.n}
        </div>
        <div className="mb-1 font-serif text-[13.5px] font-semibold text-ink">{step.title}</div>
        <div
          className={
            "text-[11.5px] leading-snug " + (step.highlight ? "text-em-deep" : "text-ink/60")
          }
        >
          {step.body}
        </div>
      </div>
      {!isLast && (
        <div className="rotate-90 self-center justify-self-center text-base font-semibold text-em-bright md:rotate-0">
          →
        </div>
      )}
    </>
  );
}
