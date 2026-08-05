"use client";

import { DemoBulletRow } from "@/components/landing/demo-bullet";
import { Reveal } from "@/components/landing/reveal";
import {
  DEMO_RESUME,
  PERSONA_CONTACT,
  PERSONA_EDUCATION_COURSEWORK,
  PERSONA_EDUCATION_HEADER,
  PERSONA_NAME,
  PERSONA_SKILLS,
} from "@/lib/demo-persona";
import { useSentenceDemo } from "@/lib/use-sentence-demo";

export function SentenceDemo() {
  const { selected, setSelected, get, patch } = useSentenceDemo();

  return (
    <div id="rewrite" className="mx-auto max-w-270 px-8 py-19">
      <Reveal className="mx-auto mb-11 max-w-xl text-center">
        <div className="mb-2.5 font-mono text-[11px] tracking-widest text-em-accent">
          TRY IT · LIVE DEMO
        </div>
        <h2 className="mb-2.5 text-[27px] font-semibold text-ink sm:text-[38px]">
          Every sentence, your call.
        </h2>
        <p className="text-base leading-relaxed text-ink/70">
          This is a demo resume. Click any sentence to select it, then cycle
          through three grounded rewrites, edit the words in place, or revert
          to exactly what was originally written.
        </p>
      </Reveal>
      <Reveal className="mb-4.5 text-center">
        <span className="inline-block animate-bounce rounded-full border border-em-softb bg-em-soft px-4 py-1.5 font-mono text-xs text-em-accent">
          ↓ try it · click any sentence below
        </span>
      </Reveal>
      <Reveal className="mx-auto max-w-3xl rounded border border-em-softb bg-white px-6.5 py-11 shadow-[0_12px_44px_rgba(28,27,24,.13)] sm:px-13 sm:pt-11 sm:pb-10">
        <div className="text-center font-serif text-2xl font-bold text-[#111]">
          {PERSONA_NAME}
        </div>
        <div className="mt-1 mb-4.5 text-center font-mono text-[10.5px] text-[#555]">
          {PERSONA_CONTACT}
        </div>

        <div className="mb-1.5">
          <div className="mt-3.5 mb-2.5 border-b border-[#111] pb-0.5 font-serif text-[13px] font-bold tracking-widest text-[#111]">
            EDUCATION
          </div>
          <div
            className="mb-2.5 rounded-lg border-[1.5px] border-transparent px-4 py-3 transition-colors hover:border-em-softb"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <span className="text-[13.5px] font-semibold text-ink">
                {PERSONA_EDUCATION_HEADER.title} · {PERSONA_EDUCATION_HEADER.sub}
              </span>
              <span className="font-mono text-[11.5px] text-[#8f8874]">
                {PERSONA_EDUCATION_HEADER.dates}
              </span>
            </div>
            <DemoBulletRow
              bulletKey="edu/course"
              bullet={PERSONA_EDUCATION_COURSEWORK}
              state={get("edu/course")}
              selected={selected === "edu/course"}
              onSelect={() => setSelected("edu/course")}
              onPatch={(next) => patch("edu/course", next)}
            />
          </div>
        </div>

        {DEMO_RESUME.map((section) => (
          <div key={section.heading} className="mb-1.5">
            <div className="mt-3.5 mb-2.5 border-b border-[#111] pb-0.5 font-serif text-[13px] font-bold tracking-widest text-[#111]">
              {section.heading}
            </div>
            {section.blocks.map((block) => (
              <div
                key={block.id}
                className="mb-2.5 rounded-lg border-[1.5px] border-transparent px-4 py-3 transition-colors hover:border-em-softb"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                  <span className="text-[13.5px] font-semibold text-ink">{block.title}</span>
                  {block.dates && (
                    <span className="font-mono text-[11.5px] text-[#8f8874]">
                      {block.dates}
                    </span>
                  )}
                </div>
                <div className="mt-0.5 mb-1.5 font-serif text-xs text-ink/70 italic">
                  {block.sub}
                </div>
                {block.bullets.map((bullet, i) => {
                  const key = `${block.id}/${i}`;
                  return (
                    <DemoBulletRow
                      key={key}
                      bulletKey={key}
                      bullet={bullet}
                      state={get(key)}
                      selected={selected === key}
                      onSelect={() => setSelected(key)}
                      onPatch={(next) => patch(key, next)}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        ))}

        <div className="mt-3.5 mb-2.5 border-b border-[#111] pb-0.5 font-serif text-[13px] font-bold tracking-widest text-[#111]">
          TECHNICAL SKILLS
        </div>
        <div className="mb-2.5 rounded-lg border-[1.5px] border-transparent px-4 py-3 transition-colors hover:border-em-softb">
          {PERSONA_SKILLS.map(({ label, bullet }) => {
            const key = `skills/${bullet.source}`;
            return (
              <div key={key} className="flex items-baseline gap-2 text-[13px]">
                <span className="w-36 shrink-0 font-semibold text-ink">{label}:</span>
                <div className="flex-1">
                  <DemoBulletRow
                    bulletKey={key}
                    bullet={bullet}
                    state={get(key)}
                    selected={selected === key}
                    onSelect={() => setSelected(key)}
                    onPatch={(next) => patch(key, next)}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Reveal>
      <Reveal className="mt-9 text-center text-[13px] text-[#8f8874]">
        Every rewrite above is generated from the same confirmed fact, never
        from thin air.
      </Reveal>
    </div>
  );
}
