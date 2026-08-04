"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import type { MasterResume } from "@/lib/types";

// One row on the paper. `factId` is a real <ENTITY>-<NN> id for an
// Experience/Project fact; coursework and skill-category rows have no real
// fact id in the schema, so `key` alone identifies them for hover/confirm
// purposes -- never fabricate a fact-id-looking tag for those.
export type PaperRow = {
  key: string;
  text: string;
  factId?: string;
};

export type PaperBlock = {
  key: string;
  title: string;
  sub: string;
  dates: string;
  rows: PaperRow[];
};

export type PaperSection = {
  heading: string;
  blocks: PaperBlock[];
};

export function masterToSections(master: MasterResume): PaperSection[] {
  const education: PaperSection = {
    heading: "EDUCATION",
    blocks: master.education.map((edu, i) => ({
      key: `edu-${i}`,
      title: edu.school,
      sub: [edu.degree, edu.location].filter(Boolean).join(" · "),
      dates: edu.grad_date,
      rows: edu.coursework.length
        ? [
            {
              key: `edu-${i}-coursework`,
              text: `Coursework: ${edu.coursework.join(", ")}.`,
            },
          ]
        : [],
    })),
  };

  const experience: PaperSection = {
    heading: "EXPERIENCE",
    blocks: master.experiences.map((exp) => ({
      key: exp.id,
      title: exp.title,
      sub: [exp.company, exp.location].filter(Boolean).join(" — "),
      dates: [exp.start, exp.end].filter(Boolean).join(" – "),
      rows: exp.facts.map((f) => ({ key: f.id, text: f.text, factId: f.id })),
    })),
  };

  const projects: PaperSection = {
    heading: "PROJECTS",
    blocks: master.projects.map((p) => ({
      key: p.id,
      title: p.name,
      sub: p.tech.join(" · "),
      dates: "",
      rows: p.facts.map((f) => ({ key: f.id, text: f.text, factId: f.id })),
    })),
  };

  const skillCategories = Object.entries(master.skills);
  const skills: PaperSection = {
    heading: "TECHNICAL SKILLS",
    blocks: skillCategories.length
      ? [
          {
            key: "skills",
            title: "",
            sub: "",
            dates: "",
            rows: skillCategories.map(([category, items]) => ({
              key: `skills-${category}`,
              text: `${category}: ${items.join(", ")}.`,
            })),
          },
        ]
      : [],
  };

  return [education, experience, projects, skills].filter((s) => s.blocks.length);
}

export function ResumePaper({
  master,
  name,
  contact,
  hoveredKey,
  onHoverRow,
  onClickRow,
  activeSectionHeading,
  compact = false,
  renderRowExtra,
}: {
  master: MasterResume;
  name: string;
  contact: string;
  hoveredKey?: string | null;
  onHoverRow?: (key: string | null) => void;
  onClickRow?: (row: PaperRow) => void;
  activeSectionHeading?: string;
  compact?: boolean;
  renderRowExtra?: (row: PaperRow) => ReactNode;
}) {
  const sections = masterToSections(master);

  return (
    <div>
      <div
        className={cn(
          "text-center font-serif font-bold text-[#111]",
          compact ? "text-lg" : "text-2xl"
        )}
      >
        {name}
      </div>
      <div
        className={cn(
          "text-center font-mono text-[#555]",
          compact ? "mt-0.5 mb-3 text-[8.5px]" : "mt-1 mb-4.5 text-[10.5px]"
        )}
      >
        {contact}
      </div>

      {sections.map((section) => (
        <div key={section.heading}>
          <div
            className={cn(
              "border-b border-[#111] font-serif font-bold tracking-widest text-[#111]",
              compact ? "mt-2.75 mb-1.5 pb-px text-[10px]" : "mt-3.5 mb-2.5 pb-0.5 text-[13px]"
            )}
          >
            {section.heading}
          </div>
          {section.blocks.map((block) => (
            <div
              key={block.key}
              className={cn(
                "rounded-lg border-[1.5px] border-transparent transition-colors",
                compact ? "mb-1.75 px-1 py-1" : "mb-2.5 px-4 py-3",
                !compact && activeSectionHeading === section.heading && "border-em-softb bg-em-soft/40",
                !compact && activeSectionHeading && activeSectionHeading !== section.heading && "opacity-100"
              )}
            >
              {block.title && (
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span
                    className={cn(
                      "font-semibold text-ink",
                      compact ? "text-[10px]" : "text-[13.5px]"
                    )}
                  >
                    {block.title}
                  </span>
                  {block.dates && (
                    <span
                      className={cn(
                        "font-mono text-[#8f8874]",
                        compact ? "text-[8.5px]" : "text-[11.5px]"
                      )}
                    >
                      {block.dates}
                    </span>
                  )}
                </div>
              )}
              {block.sub && (
                <div
                  className={cn(
                    "font-serif text-ink/70 italic",
                    compact ? "text-[9.5px]" : "mt-0.5 mb-1.5 text-xs"
                  )}
                >
                  {block.sub}
                </div>
              )}
              {block.rows.map((row) => (
                <div
                  key={row.key}
                  onMouseEnter={() => onHoverRow?.(row.key)}
                  onMouseLeave={() => onHoverRow?.(null)}
                  onClick={() => onClickRow?.(row)}
                  className={cn(
                    "-mx-1.75 flex items-baseline gap-1.75 rounded-md px-1.75 py-0.5 transition-colors",
                    onClickRow && "cursor-pointer",
                    hoveredKey === row.key && "bg-em-soft"
                  )}
                >
                  <span className={compact ? "text-[9.5px] text-[#666]" : "text-[12.5px] text-[#666]"}>
                    •
                  </span>
                  <span
                    className={cn(
                      "flex-1 text-[#333]",
                      compact ? "text-[9.5px] leading-relaxed" : "text-[13px] leading-relaxed"
                    )}
                  >
                    {row.text}
                  </span>
                  {renderRowExtra?.(row)}
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
