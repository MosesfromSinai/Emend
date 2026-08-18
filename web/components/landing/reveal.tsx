"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

// fade-up on scroll into view, replaying every time — ported from the design
// component's IntersectionObserver logic (Standard motion, replay on)
export function Reveal({
  children,
  className,
  delayMs = 0,
}: {
  children: ReactNode;
  className?: string;
  delayMs?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { threshold: 0.12 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delayMs}ms` }}
      className={cn(
        "transition-all duration-[850ms] ease-[cubic-bezier(.2,.7,.3,1)]",
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-[30px]",
        // every landing section uses this for its scroll-in animation --
        // unconditional for a vestibular-disorder user with the OS-level
        // reduced-motion preference set. Content still appears (just
        // without the fade/translate), purely via CSS, so it can't get
        // stuck invisible even if the visibility state above never fires.
        "motion-reduce:translate-y-0 motion-reduce:opacity-100 motion-reduce:transition-none",
        className
      )}
    >
      {children}
    </div>
  );
}
