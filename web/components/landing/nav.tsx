"use client";

import { useState } from "react";
import Link from "next/link";

import { EmendLockup } from "@/components/emend-mark";

const LINKS = [
  { href: "#how", label: "How it works" },
  { href: "#polish", label: "Just format it" },
  { href: "#rewrite", label: "Your words" },
  { href: "#what", label: "What it is" },
];

export function LandingNav() {
  const [open, setOpen] = useState(false);

  return (
    <div className="sticky top-0 z-50 border-b border-em-softb/60 bg-paper/90 backdrop-blur">
      <div className="mx-auto flex max-w-270 items-center justify-between px-8 py-3.5">
        <EmendLockup />
        <div className="flex items-center gap-6">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="hidden text-sm text-ink/70 hover:text-ink sm:inline"
            >
              {link.label}
            </a>
          ))}
          <Link
            href="/app"
            className="rounded-lg bg-em-accent px-4.5 py-2 text-sm font-semibold text-paper shadow-[0_2px_10px_rgba(138,58,48,.35)] hover:bg-em-deep"
          >
            Get started
          </Link>
          {/* below sm, the in-page links above are hidden entirely -- this
              is the only way to reach them on a phone-width viewport */}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="landing-nav-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            className="flex h-8 w-8 flex-col items-center justify-center gap-1 sm:hidden"
          >
            <span
              className={`h-0.5 w-5 bg-ink transition-transform ${open ? "translate-y-1.5 rotate-45" : ""}`}
            />
            <span className={`h-0.5 w-5 bg-ink transition-opacity ${open ? "opacity-0" : ""}`} />
            <span
              className={`h-0.5 w-5 bg-ink transition-transform ${open ? "-translate-y-1.5 -rotate-45" : ""}`}
            />
          </button>
        </div>
      </div>
      {open && (
        <div
          id="landing-nav-menu"
          className="flex flex-col gap-3.5 border-t border-em-softb/60 px-8 py-4 sm:hidden"
        >
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="text-sm text-ink/70 hover:text-ink"
            >
              {link.label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
