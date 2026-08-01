import Link from "next/link";

// Placeholder root — the marketing landing page (Emend Landing v2) lands in
// the next phase. The product itself lives under /app.
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="font-serif text-4xl font-semibold">Emend</h1>
      <p className="max-w-md text-ink/70">
        A tailored resume that can&apos;t lie about you.
      </p>
      <Link
        href="/app"
        className="rounded-lg bg-ink px-6 py-3 font-medium text-paper hover:bg-em-deep"
      >
        Get started
      </Link>
    </main>
  );
}
