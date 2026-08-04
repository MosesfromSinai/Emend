import Link from "next/link";
import { Suspense } from "react";

import { AppStepper } from "@/components/app-stepper";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-em-line bg-paper/94 backdrop-blur-sm">
        <div className="mx-auto flex max-w-390 items-center gap-6 px-7 py-3">
          <Link href="/app" className="flex items-center gap-2.25">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-ink font-serif text-[13px] font-bold text-paper">
              E
            </span>
            <span className="font-serif text-[17px] font-semibold text-ink">Emend</span>
          </Link>
          <Suspense fallback={null}>
            <AppStepper />
          </Suspense>
          <Link href="/app/history" className="ml-auto text-[12.5px] font-medium text-ink/70 hover:text-ink">
            History
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-390 px-7 py-8">{children}</main>
    </div>
  );
}
