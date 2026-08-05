import Link from "next/link";

export function LandingNav() {
  return (
    <div className="sticky top-0 z-50 border-b border-em-softb/60 bg-paper/90 backdrop-blur">
      <div className="mx-auto flex max-w-270 items-center justify-between px-8 py-3.5">
        <span className="font-serif text-xl font-semibold text-ink">Emend</span>
        <div className="flex items-center gap-6">
          <a href="#how" className="hidden text-sm text-ink/70 hover:text-ink sm:inline">
            How it works
          </a>
          <a
            href="#rewrite"
            className="hidden text-sm text-ink/70 hover:text-ink sm:inline"
          >
            Your words
          </a>
          <a href="#what" className="hidden text-sm text-ink/70 hover:text-ink sm:inline">
            What it is
          </a>
          <Link
            href="/app"
            className="rounded-lg bg-em-accent px-4.5 py-2 text-sm font-semibold text-paper shadow-[0_2px_10px_rgba(138,58,48,.35)] hover:bg-em-deep"
          >
            Get started
          </Link>
        </div>
      </div>
    </div>
  );
}
