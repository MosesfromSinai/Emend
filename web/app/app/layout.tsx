import Link from "next/link";
import { Suspense } from "react";

import { AppStepper } from "@/components/app-stepper";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    // The header sits OUTSIDE the scrolling area entirely (a non-shrinking
    // flex sibling above <main>, not a sticky element within a scrolling
    // page) so <main> is the one and only scroll container. Pages that want
    // a viewport-locked, no-outer-scroll layout (Confirm, Export) can size
    // themselves with a plain `h-full` and never need to guess the header's
    // pixel height -- flexbox already accounts for it. Pages with ordinary
    // content just get a normal scrollbar on <main> when they overflow it,
    // which looks identical to the page itself scrolling.
    <div className="flex h-screen flex-col">
      <header className="z-40 shrink-0 border-b border-em-line bg-paper/94 backdrop-blur-sm">
        <div className="mx-auto flex max-w-390 items-center gap-6 px-7 py-3">
          <Link href="/" className="text-[12.5px] font-medium text-ink/60 hover:text-ink">
            ← Back to home
          </Link>
          <Link href="/app" className="font-serif text-[17px] font-semibold text-ink">
            Emend
          </Link>
          <Suspense fallback={null}>
            <AppStepper />
          </Suspense>
          <Link href="/app/history" className="ml-auto text-[12.5px] font-medium text-ink/70 hover:text-ink">
            History
          </Link>
        </div>
      </header>
      <main className="mx-auto w-full max-w-390 flex-1 overflow-y-auto px-7 py-8">{children}</main>
    </div>
  );
}
