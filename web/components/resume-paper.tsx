"use client";

import { Fragment, type KeyboardEvent, type ReactNode } from "react";

import { reorderByKey } from "@/lib/order";
import { cn } from "@/lib/utils";
import { FactTag } from "@/components/ui/fact-tag";
import type { MasterResume } from "@/lib/types";

// mirrors latex/render.py's DEFAULT_SECTION_ORDER
export const DEFAULT_SECTION_ORDER = ["EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS"];

// The one hover cue for "click this line to edit it" -- a soft red
// highlight, same tone as the delete X and the active editor's own border,
// so hovering previews the same "this is editable" signal every clickable
// line in Export shares, before you've clicked anything.
const EDITABLE_HOVER = "cursor-pointer rounded px-1 -mx-1 hover:bg-red-50 hover:text-red-900";

// Every "click this line to edit it" target below used to be a plain
// div/span with only onClick -- no role, no tabIndex, no keyboard handler,
// so a keyboard-only user couldn't open a single editor anywhere in the
// app (this is the entire editing mechanism on both Confirm and Export).
// Spread onto an element alongside its onClick; returns {} (no a11y props
// added) when there's no handler, matching each call site's existing
// "only interactive when this specific thing is actually editable" logic.
function editableProps(onActivate?: () => void) {
  if (!onActivate) return {};
  return {
    role: "button" as const,
    tabIndex: 0,
    onKeyDown: (e: KeyboardEvent) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      e.preventDefault();
      onActivate();
    },
  };
}

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
  // text_overrides paths backing each displayed line -- empty means that
  // line has nothing to edit (e.g. a project has no dates line at all).
  // A line can represent more than one underlying field (company + location
  // shown as one "sub" line), so each is a list, not a single key.
  titleOverrideKeys: string[];
  subOverrideKeys: string[];
  datesOverrideKeys: string[];
};

export type PaperSection = {
  // stable identifier matching DEFAULT_SECTION_ORDER -- `heading` is just
  // display text ("TECHNICAL SKILLS" vs. the key "SKILLS") and isn't safe
  // to reorder against
  key: string;
  heading: string;
  // text_overrides path for renaming the printed heading -- "Experience"
  // to "Leadership", say -- without touching the section's actual key/order
  headingOverrideKey: string;
  blocks: PaperBlock[];
};

export function masterToSections(
  master: MasterResume,
  sectionOrder: string[] = [],
  // keyed by DEFAULT_SECTION_ORDER's own keys -- there's no field on
  // MasterResume for a section heading (unlike title/company/etc., which
  // all come from real resume data), so this is the only path an override
  // can reach the on-screen preview through.
  sectionHeadings: Record<string, string> = {}
): PaperSection[] {
  const education: PaperSection = {
    key: "EDUCATION",
    heading: sectionHeadings.EDUCATION ?? "EDUCATION",
    headingOverrideKey: "section:EDUCATION:heading",
    blocks: master.education.map((edu, i) => ({
      key: `edu-${i}`,
      title: edu.school,
      sub: [edu.degree, edu.location].filter(Boolean).join(" · "),
      dates: edu.grad_date,
      titleOverrideKeys: [`education:${i}:school`],
      subOverrideKeys: [`education:${i}:degree`, `education:${i}:location`],
      datesOverrideKeys: [`education:${i}:grad_date`],
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
    heading: sectionHeadings.EXPERIENCE ?? "EXPERIENCE",
    headingOverrideKey: "section:EXPERIENCE:heading",
    blocks: master.experiences.map((exp) => ({
      key: exp.id,
      title: exp.title,
      sub: [exp.company, exp.location].filter(Boolean).join(" — "),
      dates: [exp.start, exp.end].filter(Boolean).join(" – "),
      titleOverrideKeys: [`experience:${exp.id}:title`],
      subOverrideKeys: [`experience:${exp.id}:company`, `experience:${exp.id}:location`],
      datesOverrideKeys: [`experience:${exp.id}:start`, `experience:${exp.id}:end`],
      rows: exp.facts.map((f) => ({ key: f.id, text: f.text, factId: f.id })),
    })),
  };

  const projects: PaperSection = {
    key: "PROJECTS",
    heading: sectionHeadings.PROJECTS ?? "PROJECTS",
    headingOverrideKey: "section:PROJECTS:heading",
    blocks: master.projects.map((p) => ({
      key: p.id,
      title: p.name,
      sub: p.tech.join(" · "),
      dates: "",
      titleOverrideKeys: [`project:${p.id}:name`],
      subOverrideKeys: [`project:${p.id}:tech`],
      datesOverrideKeys: [],
      rows: p.facts.map((f) => ({ key: f.id, text: f.text, factId: f.id })),
    })),
  };

  // An override clearing a category to "" means "delete this category" --
  // previously the empty category stayed in the list and rendered as a
  // dangling "Category: " label with nothing after it.
  const nonEmptySkillCategories = Object.entries(master.skills).filter(
    ([, items]) => items.length
  );
  const skills: PaperSection = {
    key: "SKILLS",
    heading: sectionHeadings.SKILLS ?? "TECHNICAL SKILLS",
    headingOverrideKey: "section:SKILLS:heading",
    blocks: nonEmptySkillCategories.length
      ? [
          {
            key: "skills",
            title: "",
            sub: "",
            dates: "",
            titleOverrideKeys: [],
            subOverrideKeys: [],
            datesOverrideKeys: [],
            rows: nonEmptySkillCategories.map(([category, items]) => ({
              key: `skills-${category}`,
              text: `${category}: ${items.join(", ")}.`,
              overrideKey: `skills:${category}`,
            })),
          },
        ]
      : [],
  };

  // custom sections are per-resume, not a fixed set like the four above --
  // never AI-tailored, so every field here is always free-text editable,
  // same as Education
  const customSections: PaperSection[] = master.custom_sections.map((cs) => ({
    key: cs.key,
    heading: sectionHeadings[cs.key] ?? cs.heading,
    headingOverrideKey: `section:${cs.key}:heading`,
    blocks: cs.entries.map((entry) => ({
      key: entry.id,
      title: entry.title,
      sub: [entry.subtitle, entry.location].filter(Boolean).join(" — "),
      dates: [entry.start, entry.end].filter(Boolean).join(" – "),
      titleOverrideKeys: [`custom:${entry.id}:title`],
      subOverrideKeys: [`custom:${entry.id}:subtitle`, `custom:${entry.id}:location`],
      datesOverrideKeys: [`custom:${entry.id}:start`, `custom:${entry.id}:end`],
      // An override clearing a fact to "" means "delete this bullet" (same
      // convention as skills above) -- previously it stayed in the list
      // and rendered as a bare, textless bullet point.
      rows: entry.facts
        .filter((f) => f.text)
        .map((f) => ({
          key: f.id,
          text: f.text,
          factId: f.id,
          overrideKey: `custom:${entry.id}:fact:${f.id}`,
        })),
    })),
  }));

  const visible = [education, experience, projects, skills, ...customSections].filter(
    (s) => s.blocks.length
  );
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
  activeRowKey,
  renderRowControl,
  renderRowExtra,
  renderBlockControl,
  renderSectionControl,
  sectionOrder,
  activeBlockField,
  onClickBlockField,
  renderBlockFieldControl,
  activeHeaderField,
  onClickHeaderField,
  renderHeaderFieldControl,
  activeSectionHeadingKey,
  onClickSectionHeading,
  renderSectionHeadingControl,
  sectionHeadings,
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
  // matched against a row's own `key` -- the click-to-edit affordance for
  // rows with no fact id (coursework, skills), separate from activeFactId
  activeRowKey?: string | null;
  renderRowControl?: (row: PaperRow) => ReactNode;
  renderRowExtra?: (row: PaperRow) => ReactNode;
  // move/delete controls only -- editing a block's title/sub/dates happens
  // by clicking those lines directly, see activeBlockField below
  renderBlockControl?: (block: PaperBlock) => ReactNode;
  renderSectionControl?: (section: PaperSection) => ReactNode;
  sectionOrder?: string[];
  // click-to-edit for a block's title/sub/dates line -- each is one visual
  // line even when it represents more than one text_overrides key (e.g.
  // "sub" is company + location), matching "click any line to edit"
  activeBlockField?: { blockKey: string; field: "title" | "sub" | "dates" } | null;
  onClickBlockField?: (block: PaperBlock, field: "title" | "sub" | "dates") => void;
  renderBlockFieldControl?: (block: PaperBlock, field: "title" | "sub" | "dates") => ReactNode;
  // same idea for the name/contact header lines, which aren't a PaperBlock
  activeHeaderField?: "name" | "contact" | null;
  onClickHeaderField?: (field: "name" | "contact") => void;
  renderHeaderFieldControl?: (field: "name" | "contact") => ReactNode;
  // click-to-edit for a section's own printed heading ("Experience" ->
  // "Leadership") -- matched against the section's key, not its (already
  // possibly overridden) heading text
  activeSectionHeadingKey?: string | null;
  onClickSectionHeading?: (section: PaperSection) => void;
  renderSectionHeadingControl?: (section: PaperSection) => ReactNode;
  sectionHeadings?: Record<string, string>;
}) {
  const sections = masterToSections(master, sectionOrder, sectionHeadings);
  const isExport = size === "export";

  return (
    <div>
      <div
        className={cn(
          "text-center font-serif font-bold text-[#111]",
          isExport ? "text-[27px]" : "text-2xl",
          onClickHeaderField && EDITABLE_HOVER
        )}
        onClick={() => onClickHeaderField?.("name")}
        {...editableProps(onClickHeaderField && (() => onClickHeaderField("name")))}
      >
        {name}
      </div>
      {activeHeaderField === "name" && renderHeaderFieldControl?.("name")}
      <div
        className={cn(
          "mt-1 mb-4.5 text-center font-mono text-[10.5px] text-[#555]",
          onClickHeaderField && EDITABLE_HOVER
        )}
        onClick={() => onClickHeaderField?.("contact")}
        {...editableProps(onClickHeaderField && (() => onClickHeaderField("contact")))}
      >
        {contact}
      </div>
      {activeHeaderField === "contact" && renderHeaderFieldControl?.("contact")}

      {sections.map((section) => (
        <div key={section.key} data-section-key={section.key} data-section-heading={section.heading}>
          <div className="mt-3.5 mb-2.5 flex items-center justify-between border-b border-[#111] pb-0.5">
            <span
              className={cn(
                "font-serif text-[13px] font-bold tracking-widest text-[#111]",
                onClickSectionHeading && EDITABLE_HOVER
              )}
              onClick={() => onClickSectionHeading?.(section)}
              {...editableProps(onClickSectionHeading && (() => onClickSectionHeading(section)))}
            >
              {section.heading}
            </span>
            {renderSectionControl?.(section)}
          </div>
          {activeSectionHeadingKey === section.key && renderSectionHeadingControl?.(section)}
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
                  <span
                    className={cn(
                      "text-[13.5px] font-semibold text-ink",
                      block.titleOverrideKeys.length > 0 &&
                        onClickBlockField &&
                        EDITABLE_HOVER
                    )}
                    onClick={() =>
                      block.titleOverrideKeys.length > 0 && onClickBlockField?.(block, "title")
                    }
                    {...editableProps(
                      block.titleOverrideKeys.length > 0 && onClickBlockField
                        ? () => onClickBlockField(block, "title")
                        : undefined
                    )}
                  >
                    {block.title}
                  </span>
                  <span className="flex items-center gap-2">
                    {block.dates && (
                      <span
                        className={cn(
                          "font-mono text-[11.5px] text-[#8f8874]",
                          block.datesOverrideKeys.length > 0 &&
                            onClickBlockField &&
                            EDITABLE_HOVER
                        )}
                        onClick={() =>
                          block.datesOverrideKeys.length > 0 && onClickBlockField?.(block, "dates")
                        }
                        {...editableProps(
                          block.datesOverrideKeys.length > 0 && onClickBlockField
                            ? () => onClickBlockField(block, "dates")
                            : undefined
                        )}
                      >
                        {block.dates}
                      </span>
                    )}
                    {renderBlockControl?.(block)}
                  </span>
                </div>
              )}
              {activeBlockField?.blockKey === block.key && activeBlockField.field === "title" &&
                renderBlockFieldControl?.(block, "title")}
              {activeBlockField?.blockKey === block.key && activeBlockField.field === "dates" &&
                renderBlockFieldControl?.(block, "dates")}
              {block.sub && (
                <div
                  className={cn(
                    "mt-0.5 mb-1.5 text-xs font-serif text-ink/70 italic",
                    block.subOverrideKeys.length > 0 &&
                      onClickBlockField &&
                      EDITABLE_HOVER
                  )}
                  onClick={() =>
                    block.subOverrideKeys.length > 0 && onClickBlockField?.(block, "sub")
                  }
                  {...editableProps(
                    block.subOverrideKeys.length > 0 && onClickBlockField
                      ? () => onClickBlockField(block, "sub")
                      : undefined
                  )}
                >
                  {block.sub}
                </div>
              )}
              {activeBlockField?.blockKey === block.key && activeBlockField.field === "sub" &&
                renderBlockFieldControl?.(block, "sub")}
              {block.rows.map((row) => (
                <Fragment key={row.key}>
                  <div
                    onMouseEnter={() => onHoverRow?.(row.key)}
                    onMouseLeave={() => onHoverRow?.(null)}
                    onClick={() => onClickRow?.(row)}
                    {...editableProps(onClickRow && (() => onClickRow(row)))}
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
                  {((row.factId !== undefined && row.factId === activeFactId) ||
                    (row.overrideKey !== undefined && row.key === activeRowKey)) &&
                    renderRowControl?.(row)}
                </Fragment>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
