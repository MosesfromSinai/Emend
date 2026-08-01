import Link from "next/link";

export function LandingNav() {
  return (
    <div className="sticky top-0 z-50 border-b border-em-softb/60 bg-paper/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1080px] items-center justify-between px-8 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-[26px] w-[26px] items-center justify-center rounded-[5px] bg-ink font-serif text-sm font-bold text-paper">
            E
          </div>
          <span className="font-serif text-lg font-semibold text-ink">Emend</span>
        </div>
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
            className="rounded-lg bg-ink px-4.5 py-2 text-sm font-semibold text-paper hover:bg-em-deep"
          >
            Get started
          </Link>
        </div>
      </div>
    </div>
  );
}
