"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

const STEPS = [
  { key: "import", label: "Import", href: "/app" },
  // Not directly linkable -- there's no reload path for an in-progress
  // confirm session, only a fresh extraction (extractFacts/extractFromFile
  // in web/app/app/page.tsx) can reach this step. Reflects the active step
  // via currentStepKey below once the page pushes ?step=confirm itself.
  { key: "confirm", label: "Confirm facts", href: null },
  { key: "tailor", label: "Tailor", href: "/app/workspace" },
  { key: "export", label: "Export", href: null },
] as const;

function currentStepKey(pathname: string, step: string | null): string {
  if (pathname.startsWith("/app/applications/")) return "export";
  if (pathname === "/app/workspace") return "tailor";
  if (pathname === "/app" && step === "confirm") return "confirm";
  if (pathname === "/app") return "import";
  return "";
}

export function AppStepper() {
  const pathname = usePathname();
  const current = currentStepKey(pathname, useSearchParams().get("step"));
  const currentIndex = STEPS.findIndex((s) => s.key === current);

  return (
    <div className="ml-2 flex shrink-0 items-center gap-1">
      {STEPS.map((step, index) => {
        const isActive = step.key === current;
        const isDone = currentIndex >= 0 && index < currentIndex;
        const clickable = step.href && !isActive;

        const pill = (
          <span
            className={
              "flex items-center gap-1.75 rounded-full px-3.25 py-1.75 text-xs font-semibold transition-colors " +
              (isActive
                ? "bg-em-accent text-paper"
                : isDone
                  ? "text-ink"
                  : "text-em-faint") +
              (clickable ? " hover:bg-em-soft" : "")
            }
          >
            <span
              className={
                "flex h-4.25 w-4.25 items-center justify-center rounded-full font-mono text-[9.5px] font-semibold " +
                (isActive
                  ? "bg-em-bright text-code-pane"
                  : isDone
                    ? "bg-em-ok-bg text-em-ok-fg"
                    : "bg-em-line-2 text-em-faint")
              }
            >
              {index + 1}
            </span>
            <span className="hidden sm:inline">{step.label}</span>
          </span>
        );

        return clickable ? (
          <Link key={step.key} href={step.href!}>
            {pill}
          </Link>
        ) : (
          <span key={step.key}>{pill}</span>
        );
      })}
    </div>
  );
}
