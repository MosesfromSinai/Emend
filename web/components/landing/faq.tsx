"use client";

import { useState } from "react";
import { Reveal } from "@/components/landing/reveal";
import { DEMO_FAQS } from "@/lib/demo-persona";

export function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="border-t border-em-softb bg-white">
      <div className="mx-auto max-w-180 px-8 py-18">
        <Reveal className="mb-9 text-center">
          <div className="mb-2.5 font-mono text-[11px] tracking-[.12em] text-em-accent">
            FAQ
          </div>
          <h2 className="text-[27px] font-semibold text-ink sm:text-[34px]">Fair questions.</h2>
        </Reveal>
        <Reveal className="flex flex-col gap-2.5">
          {DEMO_FAQS.map((faq, i) => {
            const isOpen = open === i;
            return (
              <div
                key={faq.q}
                className="overflow-hidden rounded-[10px] border border-em-softb bg-paper"
              >
                <button
                  onClick={() => setOpen(isOpen ? null : i)}
                  className="flex w-full items-center justify-between gap-3.5 px-5 py-4 text-left font-serif text-[15px] font-semibold text-ink hover:bg-[#f4f0e6]"
                >
                  {faq.q}
                  <span className="shrink-0 text-lg text-em-accent">
                    {isOpen ? "−" : "+"}
                  </span>
                </button>
                {isOpen && (
                  <div className="px-5 pb-4 text-sm leading-relaxed text-ink/70">{faq.a}</div>
                )}
              </div>
            );
          })}
        </Reveal>
      </div>
    </div>
  );
}
