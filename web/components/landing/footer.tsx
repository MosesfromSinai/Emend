const PRODUCT_LINKS = [
  { href: "#how", label: "How it works" },
  { href: "#rewrite", label: "Your words" },
  { href: "#what", label: "What it is" },
];

// "Get started", not "Account" — there's no auth yet (see the brief's
// reconciliation #2), so this column links to what actually exists rather
// than a sign-in flow that doesn't.
const GET_STARTED_LINKS = [
  { href: "/app/workspace", label: "Tailor my resume" },
  { href: "/app", label: "Upload existing resume" },
];

const LEGAL_LINKS = [
  { href: "#", label: "Privacy policy" },
  { href: "#", label: "Terms of service" },
];

function FooterColumn({
  heading,
  links,
}: {
  heading: string;
  links: { href: string; label: string }[];
}) {
  return (
    <div className="flex flex-col gap-2.25">
      <div className="mb-0.5 text-xs font-semibold text-ink">{heading}</div>
      {links.map((link) => (
        <a
          key={link.label}
          href={link.href}
          className="text-[13px] text-ink/70 hover:text-ink"
        >
          {link.label}
        </a>
      ))}
    </div>
  );
}

export function Footer() {
  return (
    <div className="border-t border-em-softb bg-paper">
      <div className="mx-auto grid max-w-270 grid-cols-1 gap-8 px-8 py-12 sm:grid-cols-[2fr_1fr_1fr_1fr]">
        <div>
          <div className="mb-2.5 flex items-center gap-2.25">
            <div className="flex h-5.5 w-5.5 items-center justify-center rounded bg-ink font-serif text-xs font-bold text-paper">
              E
            </div>
            <span className="font-serif text-base font-semibold text-ink">Emend</span>
          </div>
          <p className="max-w-60 text-[13px] leading-relaxed text-ink/60">
            Grounded, LaTeX-typeset resume tailoring. Every line traceable to
            your real experience.
          </p>
        </div>
        <FooterColumn heading="Product" links={PRODUCT_LINKS} />
        <FooterColumn heading="Get started" links={GET_STARTED_LINKS} />
        <FooterColumn heading="Legal" links={LEGAL_LINKS} />
      </div>
      <div className="mx-auto max-w-270 px-8 pb-7 text-xs text-[#a89f8c]">
        © 2026 Emend. All rights reserved.
      </div>
    </div>
  );
}
