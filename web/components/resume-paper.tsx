"use client";

import { Fragment, type ReactNode } from "react";

import { cn } from "@/lib/utils";
import { FactTag } from "@/components/ui/fact-tag";
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
  size = "default",
  confirmedKeys,
  activeFactId,
  renderRowControl,
  renderRowExtra,
  renderBlockControl,
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
}) {
  const sections = masterToSections(master);
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
        <div key={section.heading}>
          <div className="mt-3.5 mb-2.5 border-b border-[#111] pb-0.5 font-serif text-[13px] font-bold tracking-widest text-[#111]">
            {section.heading}
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
                  {block.dates && (
                    <span className="font-mono text-[11.5px] text-[#8f8874]">{block.dates}</span>
                  )}
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
