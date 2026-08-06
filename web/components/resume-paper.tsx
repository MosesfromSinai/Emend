"use client";

import { Fragment, type ReactNode } from "react";

import { reorderByKey } from "@/lib/order";
import { cn } from "@/lib/utils";
import { FactTag } from "@/components/ui/fact-tag";
import type { MasterResume } from "@/lib/types";

// mirrors latex/render.py's DEFAULT_SECTION_ORDER
export const DEFAULT_SECTION_ORDER = ["EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS"];

// One row on the paper. `factId` is a real <ENTITY>-<NN> id for an
// Experience/Project fact; coursework and skill-category rows have no real
// fact id in the schema, so `key` alone identifies them for hover/confirm
// purposes -- never fabricate a fact-id-looking tag for those.
export type PaperRow = {
  key: string;
  text: string;
  factId?: string;
  // stable text_overrides path (mirrors api's RenderRequest.text_overrides)
  // for rows with no fact id -- coursework and skills lines are confirmed
  // master data, editable as free text, not grounded generated content.
  overrideKey?: string;
};

export type PaperBlock = {
  key: string;
  title: string;
  sub: string;
  dates: string;
  rows: PaperRow[];
};

export type PaperSection = {
  // stable identifier matching DEFAULT_SECTION_ORDER -- `heading` is just
  // display text ("TECHNICAL SKILLS" vs. the key "SKILLS") and isn't safe
  // to reorder against
  key: string;
  heading: string;
  blocks: PaperBlock[];
};

export function masterToSections(
  master: MasterResume,
  sectionOrder: string[] = []
): PaperSection[] {
  const education: PaperSection = {
    key: "EDUCATION",
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
              overrideKey: `education:${i}:coursework`,
            },
          ]
        : [],
    })),
  };

  const experience: PaperSection = {
    key: "EXPERIENCE",
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
    key: "PROJECTS",
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
    key: "SKILLS",
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

  const visible = [education, experience, projects, skills].filter((s) => s.blocks.length);
  return reorderByKey(visible, sectionOrder, (s) => s.key);
}

export function ResumePaper({
  master,
  name,
  contact,
  hoveredKey,
  onHoverRow,
  onClickRow,
  activeSectionHeading,
  size = "default",
  confirmedKeys,
  activeFactId,
  renderRowControl,
  renderRowExtra,
  renderBlockControl,
  renderSectionControl,
  sectionOrder,
}: {
  master: MasterResume;
  name: string;
  contact: string;
  hoveredKey?: string | null;
  onHoverRow?: (key: string | null) => void;
  onClickRow?: (row: PaperRow) => void;
  activeSectionHeading?: string;
  size?: "default" | "export";
  confirmedKeys?: Set<string>;
  activeFactId?: string | null;
  renderRowControl?: (row: PaperRow) => ReactNode;
  renderRowExtra?: (row: PaperRow) => ReactNode;
  renderBlockControl?: (block: PaperBlock) => ReactNode;
  renderSectionControl?: (section: PaperSection) => ReactNode;
  sectionOrder?: string[];
}) {
  const sections = masterToSections(master, sectionOrder);
  const isExport = size === "export";

  return (
    <div>
      <div
        className={cn(
          "text-center font-serif font-bold text-[#111]",
          isExport ? "text-[27px]" : "text-2xl"
        )}
      >
        {name}
      </div>
      <div className="mt-1 mb-4.5 text-center font-mono text-[10.5px] text-[#555]">{contact}</div>

      {sections.map((section) => (
        <div key={section.key}>
          <div className="mt-3.5 mb-2.5 flex items-center justify-between border-b border-[#111] pb-0.5">
            <span className="font-serif text-[13px] font-bold tracking-widest text-[#111]">
              {section.heading}
            </span>
            {renderSectionControl?.(section)}
          </div>
          {section.blocks.map((block) => (
            <div
              key={block.key}
              className={cn(
                "mb-2.5 rounded-lg border-[1.5px] border-transparent px-4 py-3 transition-colors",
                activeSectionHeading === section.heading && "border-em-softb bg-em-soft/40"
              )}
            >
              {block.title && (
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-[13.5px] font-semibold text-ink">{block.title}</span>
                  <span className="flex items-center gap-2">
                    {block.dates && (
                      <span className="font-mono text-[11.5px] text-[#8f8874]">{block.dates}</span>
                    )}
                    {renderBlockControl?.(block)}
                  </span>
                </div>
              )}
              {block.sub && (
                <div className="mt-0.5 mb-1.5 text-xs font-serif text-ink/70 italic">
                  {block.sub}
                </div>
              )}
              {block.rows.map((row) => (
                <Fragment key={row.key}>
                  <div
                    onMouseEnter={() => onHoverRow?.(row.key)}
                    onMouseLeave={() => onHoverRow?.(null)}
                    onClick={() => onClickRow?.(row)}
                    className={cn(
                      "-mx-1.75 flex items-baseline gap-1.75 rounded-md px-1.75 py-0.5 transition-colors",
                      onClickRow && "cursor-pointer",
                      confirmedKeys?.has(row.key) && "bg-em-ok-wash",
                      hoveredKey === row.key && "bg-em-soft"
                    )}
                  >
                    <span className="text-[12.5px] text-[#666]">•</span>
                    <span
                      className={cn(
                        "flex-1 text-[#333]",
                        isExport ? "text-[12.5px] leading-[1.6]" : "text-[13px] leading-relaxed"
                      )}
                    >
                      {row.text}
                    </span>
                    {row.factId && (
                      <FactTag
                        id={row.factId}
                        className={cn("shrink-0", isExport && "text-[9.5px]")}
                      />
                    )}
                    {renderRowExtra?.(row)}
                  </div>
                  {activeFactId === row.factId && renderRowControl?.(row)}
                </Fragment>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
