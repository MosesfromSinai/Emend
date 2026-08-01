import Link from "next/link";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-em-softb/60 bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3">
          <Link href="/app" className="font-serif text-lg font-semibold">
            Emend
          </Link>
          <nav className="flex gap-5 text-sm text-ink/70">
            <Link href="/app/workspace" className="hover:text-ink">
              Workspace
            </Link>
            <Link href="/app/history" className="hover:text-ink">
              History
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-10">{children}</main>
    </div>
  );
}
