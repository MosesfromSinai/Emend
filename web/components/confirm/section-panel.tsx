"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { FactTag } from "@/components/ui/fact-tag";
import { Input } from "@/components/ui/input";
import { MonthInput } from "@/components/ui/month-input";
import { StringList } from "@/components/string-list";
import { masterToSections, type PaperSection } from "@/components/resume-paper";
import { hasMetric } from "@/lib/fact-metrics";
import { nextFactId, slugSectionId } from "@/lib/master-resume";
import { cn } from "@/lib/utils";
import type { CustomEntry, Education, Experience, Fact, MasterResume, Project } from "@/lib/types";

const RESERVED_SECTION_KEYS = new Set(["EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS"]);

export const SECTION_HEADINGS = ["EDUCATION", "EXPERIENCE", "PROJECTS", "TECHNICAL SKILLS"] as const;
export type SectionHeading = (typeof SECTION_HEADINGS)[number];

const SECTION_LABELS: Record<SectionHeading, string> = {
  EDUCATION: "Education",
  EXPERIENCE: "Experience",
  PROJECTS: "Projects",
  "TECHNICAL SKILLS": "Technical skills",
};

type Filter = "all" | "confirmed" | "needs-metric";

const FILTER_LABELS: Record<Filter, string> = {
  all: "All",
  confirmed: "Confirmed",
  "needs-metric": "Needs a metric",
};

function passesFilter(filter: Filter, text: string, confirmed: boolean): boolean {
  if (filter === "confirmed") return confirmed;
  if (filter === "needs-metric") return !hasMetric(text);
  return true;
}

// A fixed section is identified by its heading text ("TECHNICAL SKILLS",
// not the "SKILLS" key -- a pre-existing mismatch this doesn't touch); a
// custom section is identified by its own stable `key` instead of its
// heading, since the heading can be renamed right here on Confirm and a
// tab's identity must survive that rename.
function findSectionForTab(sections: PaperSection[], tab: string): PaperSection | undefined {
  return sections.find((s) => s.heading === tab || s.key === tab);
}

export function sectionTabs(master: MasterResume): string[] {
  return [...SECTION_HEADINGS, ...master.custom_sections.map((cs) => cs.key)];
}

export function sectionProgress(master: MasterResume, confirmed: Set<string>) {
  const sections = masterToSections(master);
  return sectionTabs(master).map((tab) => {
    const section = findSectionForTab(sections, tab);
    const keys = section ? section.blocks.flatMap((b) => b.rows.map((r) => r.key)) : [];
    return { heading: tab, keys, done: keys.filter((k) => confirmed.has(k)).length, total: keys.length };
  });
}

export function allRowKeys(master: MasterResume): string[] {
  return masterToSections(master).flatMap((s) => s.blocks.flatMap((b) => b.rows.map((r) => r.key)));
}

function usedSectionIds(master: MasterResume): Set<string> {
  return new Set(
    [...master.experiences, ...master.projects, ...master.custom_sections.flatMap((cs) => cs.entries)].map(
      (s) => s.id
    )
  );
}

function usedSectionKeys(master: MasterResume): Set<string> {
  return new Set([...RESERVED_SECTION_KEYS, ...master.custom_sections.map((cs) => cs.key)]);
}

export function ConfirmPill({
  confirmed,
  onToggle,
}: {
  confirmed: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn(
        "shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold transition-colors",
        confirmed
          ? "border-transparent bg-em-ok-bg text-em-ok-fg"
          : "border-em-softb text-ink/60 hover:border-ink"
      )}
    >
      {confirmed ? "✓ confirmed" : "Confirm"}
    </button>
  );
}

function MetricLine({ text }: { text: string }) {
  if (hasMetric(text) || !text.trim()) return null;
  return <p className="mt-1 text-[11px] text-em-warn-fg">Needs a metric</p>;
}

function AutoTextarea({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  return (
    <textarea
      ref={ref}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={1}
      className="w-full resize-none overflow-hidden rounded-md border border-em-softb bg-white px-2.5 py-1.5 text-sm text-ink focus:border-em-accent focus:outline-none focus:ring-1 focus:ring-em-accent"
    />
  );
}

type RowChromeProps = {
  rowKey: string;
  hovered: boolean;
  onHover: (key: string | null) => void;
  children: React.ReactNode;
};

function RowChrome({ rowKey, hovered, onHover, children }: RowChromeProps) {
  return (
    <div
      onMouseEnter={() => onHover(rowKey)}
      onMouseLeave={() => onHover(null)}
      className={cn("rounded-md p-1.5 transition-colors", hovered && "bg-em-soft/60")}
    >
      {children}
    </div>
  );
}

type SectionProps = {
  master: MasterResume;
  onChange: (master: MasterResume) => void;
  confirmed: Set<string>;
  onToggleConfirm: (key: string) => void;
  onConfirmMany: (keys: string[], value: boolean) => void;
  hoveredKey: string | null;
  onHoverRow: (key: string | null) => void;
  filter: Filter;
};

function FactRow({
  fact,
  onChangeText,
  onRemove,
  confirmed,
  onToggleConfirm,
  hovered,
  onHover,
}: {
  fact: Fact;
  onChangeText: (text: string) => void;
  onRemove: () => void;
  confirmed: boolean;
  onToggleConfirm: () => void;
  hovered: boolean;
  onHover: (key: string | null) => void;
}) {
  return (
    <RowChrome rowKey={fact.id} hovered={hovered} onHover={onHover}>
      <div className="flex items-start gap-2">
        <FactTag id={fact.id} className="mt-2" />
        <div className="flex-1">
          <AutoTextarea value={fact.text} onChange={onChangeText} />
          <MetricLine text={fact.text} />
        </div>
        <ConfirmPill confirmed={confirmed} onToggle={onToggleConfirm} />
        <button
          type="button"
          aria-label={`Remove fact ${fact.id}`}
          onClick={onRemove}
          className="mt-2 text-ink/40 hover:text-ink"
        >
          ×
        </button>
      </div>
    </RowChrome>
  );
}

function EducationPanel({
  master,
  onChange,
  confirmed,
  onToggleConfirm,
  onConfirmMany,
  hoveredKey,
  onHoverRow,
  filter,
}: SectionProps) {
  const update = (next: Education[]) => onChange({ ...master, education: next });

  // Coursework confirmation is keyed by position (`edu-${index}-coursework`),
  // so removing an entry shifts every later entry into a key that may
  // already be marked confirmed for entirely different coursework. Clear
  // every existing coursework key, then re-confirm only the ones that still
  // apply at their post-removal index.
  const removeEducation = (index: number) => {
    const oldConfirmedKeys: string[] = [];
    const newConfirmedKeys: string[] = [];
    master.education.forEach((_, i) => {
      const oldKey = `edu-${i}-coursework`;
      if (!confirmed.has(oldKey)) return;
      oldConfirmedKeys.push(oldKey);
      if (i === index) return; // the removed entry's confirmation doesn't carry over
      const newIndex = i < index ? i : i - 1;
      newConfirmedKeys.push(`edu-${newIndex}-coursework`);
    });
    onConfirmMany(oldConfirmedKeys, false);
    onConfirmMany(newConfirmedKeys, true);
    update(master.education.filter((_, i) => i !== index));
  };

  return (
    <div className="flex flex-col gap-4">
      {master.education.map((edu, index) => {
        const key = `edu-${index}-coursework`;
        const courseText = edu.coursework.join(", ");
        if (edu.coursework.length && !passesFilter(filter, courseText, confirmed.has(key))) {
          return null;
        }
        return (
          <div key={index} className="rounded-lg border border-em-softb p-4">
            <div className="mb-2 grid grid-cols-2 gap-2">
              <Input
                value={edu.school}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, school: e.target.value };
                  update(next);
                }}
                placeholder="School"
              />
              <Input
                value={edu.degree}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, degree: e.target.value };
                  update(next);
                }}
                placeholder="Degree"
              />
              <Input
                value={edu.location}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, location: e.target.value };
                  update(next);
                }}
                placeholder="Location"
              />
              <Input
                value={edu.grad_date}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, grad_date: e.target.value };
                  update(next);
                }}
                placeholder="Graduation date"
              />
            </div>
            <RowChrome rowKey={key} hovered={hoveredKey === key} onHover={onHoverRow}>
              <StringList
                items={edu.coursework}
                onChange={(coursework) => {
                  const next = [...master.education];
                  next[index] = { ...edu, coursework };
                  update(next);
                }}
                placeholder="Course"
                addLabel="Add course"
              />
              {edu.coursework.length > 0 && (
                <div className="mt-2 flex items-center justify-between">
                  <MetricLine text={courseText} />
                  <ConfirmPill confirmed={confirmed.has(key)} onToggle={() => onToggleConfirm(key)} />
                </div>
              )}
            </RowChrome>
            <button
              type="button"
              onClick={() => removeEducation(index)}
              className="mt-2 text-sm text-ink/40 hover:text-ink"
            >
              Remove
            </button>
          </div>
        );
      })}
      <Button
        type="button"
        variant="secondary"
        className="self-start"
        onClick={() =>
          update([
            ...master.education,
            { school: "", degree: "", location: "", grad_date: "", coursework: [] },
          ])
        }
      >
        + Add education
      </Button>
    </div>
  );
}

function ExperiencePanel({
  master,
  onChange,
  confirmed,
  onToggleConfirm,
  onConfirmMany,
  hoveredKey,
  onHoverRow,
  filter,
}: SectionProps) {
  const update = (next: Experience[]) => onChange({ ...master, experiences: next });

  return (
    <div className="flex flex-col gap-5">
      {master.experiences.map((exp, index) => (
        <div key={exp.id} className="rounded-lg border border-em-softb p-4">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Input
              value={exp.company}
              onChange={(e) => {
                const next = [...master.experiences];
                next[index] = { ...exp, company: e.target.value };
                update(next);
              }}
              placeholder="Company"
              className="w-auto flex-1"
            />
            <Input
              value={exp.title}
              onChange={(e) => {
                const next = [...master.experiences];
                next[index] = { ...exp, title: e.target.value };
                update(next);
              }}
              placeholder="Title"
              className="w-auto flex-1"
            />
            <MonthInput
              value={exp.start}
              onChange={(v) => {
                const next = [...master.experiences];
                next[index] = { ...exp, start: v };
                update(next);
              }}
              placeholder="Start"
            />
            <MonthInput
              value={exp.end}
              onChange={(v) => {
                const next = [...master.experiences];
                next[index] = { ...exp, end: v };
                update(next);
              }}
              placeholder="End"
              allowPresent
            />
            <button
              type="button"
              onClick={() => {
                onConfirmMany(exp.facts.map((f) => f.id), false);
                update(master.experiences.filter((_, i) => i !== index));
              }}
              className="text-sm text-ink/40 hover:text-ink"
            >
              Remove
            </button>
          </div>
          <div className="flex flex-col gap-2">
            {exp.facts
              .filter((f) => passesFilter(filter, f.text, confirmed.has(f.id)))
              .map((fact) => (
                <FactRow
                  key={fact.id}
                  fact={fact}
                  hovered={hoveredKey === fact.id}
                  onHover={onHoverRow}
                  confirmed={confirmed.has(fact.id)}
                  onToggleConfirm={() => onToggleConfirm(fact.id)}
                  onChangeText={(text) => {
                    const next = [...master.experiences];
                    next[index] = {
                      ...exp,
                      facts: exp.facts.map((f) => (f.id === fact.id ? { ...f, text } : f)),
                    };
                    update(next);
                  }}
                  onRemove={() => {
                    const next = [...master.experiences];
                    next[index] = { ...exp, facts: exp.facts.filter((f) => f.id !== fact.id) };
                    update(next);
                    onConfirmMany([fact.id], false);
                  }}
                />
              ))}
            <Button
              type="button"
              variant="ghost"
              className="self-start px-1 py-1"
              onClick={() => {
                const next = [...master.experiences];
                next[index] = {
                  ...exp,
                  facts: [
                    ...exp.facts,
                    { id: nextFactId(exp.id, exp.facts.map((f) => f.id)), text: "" },
                  ],
                };
                update(next);
              }}
            >
              + Add fact
            </Button>
          </div>
        </div>
      ))}
      <Button
        type="button"
        variant="secondary"
        className="self-start"
        onClick={() => {
          const id = slugSectionId("EXP", usedSectionIds(master));
          update([
            ...master.experiences,
            { id, company: "", title: "", location: "", start: "", end: "", facts: [] },
          ]);
        }}
      >
        + Add experience
      </Button>
    </div>
  );
}

function ProjectPanel({
  master,
  onChange,
  confirmed,
  onToggleConfirm,
  onConfirmMany,
  hoveredKey,
  onHoverRow,
  filter,
}: SectionProps) {
  const update = (next: Project[]) => onChange({ ...master, projects: next });

  return (
    <div className="flex flex-col gap-5">
      {master.projects.map((project, index) => (
        <div key={project.id} className="rounded-lg border border-em-softb p-4">
          <div className="mb-2 flex items-center gap-2">
            <Input
              value={project.name}
              onChange={(e) => {
                const next = [...master.projects];
                next[index] = { ...project, name: e.target.value };
                update(next);
              }}
              placeholder="Project name"
              className="w-auto flex-1"
            />
            <button
              type="button"
              onClick={() => {
                onConfirmMany(project.facts.map((f) => f.id), false);
                update(master.projects.filter((_, i) => i !== index));
              }}
              className="text-sm text-ink/40 hover:text-ink"
            >
              Remove
            </button>
          </div>
          <div className="mb-3">
            <StringList
              items={project.tech}
              onChange={(tech) => {
                const next = [...master.projects];
                next[index] = { ...project, tech };
                update(next);
              }}
              placeholder="Tech"
              addLabel="Add tech"
            />
          </div>
          <div className="flex flex-col gap-2">
            {project.facts
              .filter((f) => passesFilter(filter, f.text, confirmed.has(f.id)))
              .map((fact) => (
                <FactRow
                  key={fact.id}
                  fact={fact}
                  hovered={hoveredKey === fact.id}
                  onHover={onHoverRow}
                  confirmed={confirmed.has(fact.id)}
                  onToggleConfirm={() => onToggleConfirm(fact.id)}
                  onChangeText={(text) => {
                    const next = [...master.projects];
                    next[index] = {
                      ...project,
                      facts: project.facts.map((f) => (f.id === fact.id ? { ...f, text } : f)),
                    };
                    update(next);
                  }}
                  onRemove={() => {
                    const next = [...master.projects];
                    next[index] = {
                      ...project,
                      facts: project.facts.filter((f) => f.id !== fact.id),
                    };
                    update(next);
                    onConfirmMany([fact.id], false);
                  }}
                />
              ))}
            <Button
              type="button"
              variant="ghost"
              className="self-start px-1 py-1"
              onClick={() => {
                const next = [...master.projects];
                next[index] = {
                  ...project,
                  facts: [
                    ...project.facts,
                    { id: nextFactId(project.id, project.facts.map((f) => f.id)), text: "" },
                  ],
                };
                update(next);
              }}
            >
              + Add fact
            </Button>
          </div>
        </div>
      ))}
      <Button
        type="button"
        variant="secondary"
        className="self-start"
        onClick={() => {
          const id = slugSectionId("PROJ", usedSectionIds(master));
          update([...master.projects, { id, name: "", tech: [], facts: [] }]);
        }}
      >
        + Add project
      </Button>
    </div>
  );
}

// A user-named section for content outside Education/Experience/Projects/
// Skills -- cloned from ExperiencePanel's shape (title/organization/dates +
// facts), since a custom entry is structurally the same "title, org, dates,
// bullets" thing under a different label the user picked themselves.
function CustomSectionPanel({
  master,
  onChange,
  confirmed,
  onToggleConfirm,
  onConfirmMany,
  hoveredKey,
  onHoverRow,
  filter,
  sectionKey,
  onBeforeRemove,
}: SectionProps & { sectionKey: string; onBeforeRemove: () => void }) {
  const sectionIndex = master.custom_sections.findIndex((cs) => cs.key === sectionKey);
  const section = master.custom_sections[sectionIndex];
  if (!section) return null;

  const update = (entries: CustomEntry[]) => {
    const next = [...master.custom_sections];
    next[sectionIndex] = { ...section, entries };
    onChange({ ...master, custom_sections: next });
  };
  const removeSection = () => {
    // navigate off this tab BEFORE it disappears from `master` -- otherwise
    // activeSection keeps pointing at a section that no longer exists and
    // every progress/active lookup keyed on it blows up mid-render
    onBeforeRemove();
    onConfirmMany(
      section.entries.flatMap((e) => e.facts.map((f) => f.id)),
      false
    );
    onChange({
      ...master,
      custom_sections: master.custom_sections.filter((cs) => cs.key !== sectionKey),
    });
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Input
          value={section.heading}
          onChange={(e) => {
            const next = [...master.custom_sections];
            next[sectionIndex] = { ...section, heading: e.target.value };
            onChange({ ...master, custom_sections: next });
          }}
          placeholder="Section name"
          className="w-auto flex-1"
        />
        <button type="button" onClick={removeSection} className="text-sm text-ink/40 hover:text-ink">
          Remove section
        </button>
      </div>
      {section.entries.map((entry, index) => (
        <div key={entry.id} className="rounded-lg border border-em-softb p-4">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Input
              value={entry.title}
              onChange={(e) => {
                const next = [...section.entries];
                next[index] = { ...entry, title: e.target.value };
                update(next);
              }}
              placeholder="Title"
              className="w-auto flex-1"
            />
            <Input
              value={entry.subtitle}
              onChange={(e) => {
                const next = [...section.entries];
                next[index] = { ...entry, subtitle: e.target.value };
                update(next);
              }}
              placeholder="Organization"
              className="w-auto flex-1"
            />
            <MonthInput
              value={entry.start}
              onChange={(v) => {
                const next = [...section.entries];
                next[index] = { ...entry, start: v };
                update(next);
              }}
              placeholder="Start"
            />
            <MonthInput
              value={entry.end}
              onChange={(v) => {
                const next = [...section.entries];
                next[index] = { ...entry, end: v };
                update(next);
              }}
              placeholder="End"
              allowPresent
            />
            <button
              type="button"
              onClick={() => {
                onConfirmMany(entry.facts.map((f) => f.id), false);
                update(section.entries.filter((_, i) => i !== index));
              }}
              className="text-sm text-ink/40 hover:text-ink"
            >
              Remove
            </button>
          </div>
          <div className="flex flex-col gap-2">
            {entry.facts
              .filter((f) => passesFilter(filter, f.text, confirmed.has(f.id)))
              .map((fact) => (
                <FactRow
                  key={fact.id}
                  fact={fact}
                  hovered={hoveredKey === fact.id}
                  onHover={onHoverRow}
                  confirmed={confirmed.has(fact.id)}
                  onToggleConfirm={() => onToggleConfirm(fact.id)}
                  onChangeText={(text) => {
                    const next = [...section.entries];
                    next[index] = {
                      ...entry,
                      facts: entry.facts.map((f) => (f.id === fact.id ? { ...f, text } : f)),
                    };
                    update(next);
                  }}
                  onRemove={() => {
                    const next = [...section.entries];
                    next[index] = { ...entry, facts: entry.facts.filter((f) => f.id !== fact.id) };
                    update(next);
                    onConfirmMany([fact.id], false);
                  }}
                />
              ))}
            <Button
              type="button"
              variant="ghost"
              className="self-start px-1 py-1"
              onClick={() => {
                const next = [...section.entries];
                next[index] = {
                  ...entry,
                  facts: [
                    ...entry.facts,
                    { id: nextFactId(entry.id, entry.facts.map((f) => f.id)), text: "" },
                  ],
                };
                update(next);
              }}
            >
              + Add fact
            </Button>
          </div>
        </div>
      ))}
      <Button
        type="button"
        variant="secondary"
        className="self-start"
        onClick={() => {
          const id = slugSectionId(section.heading || "ENTRY", usedSectionIds(master));
          update([
            ...section.entries,
            { id, title: "", subtitle: "", location: "", start: "", end: "", facts: [] },
          ]);
        }}
      >
        + Add entry
      </Button>
    </div>
  );
}

function SkillsPanel({
  master,
  onChange,
  confirmed,
  onToggleConfirm,
  hoveredKey,
  onHoverRow,
  filter,
}: SectionProps) {
  const categories = Object.entries(master.skills);

  const setCategory = (category: string, skills: string[]) =>
    onChange({ ...master, skills: { ...master.skills, [category]: skills } });
  const renameCategory = (oldName: string, newName: string) => {
    const { [oldName]: skills, ...rest } = master.skills;
    onChange({ ...master, skills: { ...rest, [newName]: skills ?? [] } });
  };
  const removeCategory = (category: string) => {
    const { [category]: _removed, ...rest } = master.skills;
    onChange({ ...master, skills: rest });
  };

  return (
    <div className="flex flex-col gap-3">
      {categories.map(([category, skills]) => {
        const key = `skills-${category}`;
        const text = skills.join(", ");
        if (skills.length && !passesFilter(filter, text, confirmed.has(key))) return null;
        return (
          <RowChrome key={category} rowKey={key} hovered={hoveredKey === key} onHover={onHoverRow}>
            <div className="flex flex-wrap items-center gap-2">
              <Input
                value={category}
                onChange={(e) => renameCategory(category, e.target.value)}
                className="w-40"
              />
              <StringList
                items={skills}
                onChange={(next) => setCategory(category, next)}
                placeholder="Skill"
                addLabel="Add skill"
              />
              <button
                type="button"
                onClick={() => removeCategory(category)}
                className="text-sm text-ink/40 hover:text-ink"
              >
                Remove category
              </button>
            </div>
            {skills.length > 0 && (
              <div className="mt-1 flex items-center justify-between">
                <MetricLine text={text} />
                <ConfirmPill confirmed={confirmed.has(key)} onToggle={() => onToggleConfirm(key)} />
              </div>
            )}
          </RowChrome>
        );
      })}
      <Button
        type="button"
        variant="secondary"
        className="self-start"
        onClick={() => setCategory("New category", [])}
      >
        + Add category
      </Button>
    </div>
  );
}

export function SectionPanel({
  master,
  onChange,
  confirmed,
  onToggleConfirm,
  onConfirmMany,
  activeSection,
  onChangeSection,
  hoveredKey,
  onHoverRow,
}: {
  master: MasterResume;
  onChange: (master: MasterResume) => void;
  confirmed: Set<string>;
  onToggleConfirm: (key: string) => void;
  onConfirmMany: (keys: string[], value: boolean) => void;
  activeSection: string;
  onChangeSection: (section: string) => void;
  hoveredKey: string | null;
  onHoverRow: (key: string | null) => void;
}) {
  const [filter, setFilter] = useState<Filter>("all");
  const tabs = sectionTabs(master);
  const progress = sectionProgress(master, confirmed);
  const sectionIndex = tabs.indexOf(activeSection);
  // a defensive fallback, not just the happy path: activeSection can
  // briefly point at a tab that no longer exists (e.g. the instant a
  // custom section is removed, before onBeforeRemove's redirect commits)
  const active = progress[sectionIndex] ?? { heading: activeSection, keys: [], done: 0, total: 0 };
  const customSection = master.custom_sections.find((cs) => cs.key === activeSection);

  // Auto-advance the moment a section GOES complete (via "Confirm all" or
  // the last individual checkbox) -- but never on arrival at a section
  // that's already complete (e.g. navigating back with "previous"), which
  // is why this tracks a transition, not just the current state.
  const prevCompleteRef = useRef<{ section: string; complete: boolean }>({
    section: activeSection,
    complete: active.total > 0 && active.done === active.total,
  });
  useEffect(() => {
    const isComplete = active.total > 0 && active.done === active.total;
    const prev = prevCompleteRef.current;
    const justCompletedHere = prev.section === activeSection && isComplete && !prev.complete;
    prevCompleteRef.current = { section: activeSection, complete: isComplete };
    if (justCompletedHere && sectionIndex < tabs.length - 1) {
      onChangeSection(tabs[sectionIndex + 1]);
    }
  }, [active.done, active.total, activeSection, sectionIndex, onChangeSection, tabs]);
  const entryCount =
    activeSection === "EDUCATION"
      ? master.education.length
      : activeSection === "EXPERIENCE"
        ? master.experiences.length
        : activeSection === "PROJECTS"
          ? master.projects.length
          : activeSection === "TECHNICAL SKILLS"
            ? Object.keys(master.skills).length
            : (customSection?.entries.length ?? 0);

  const sectionProps: SectionProps = {
    master,
    onChange,
    confirmed,
    onToggleConfirm,
    onConfirmMany,
    hoveredKey,
    onHoverRow,
    filter,
  };

  return (
    <div className="flex min-h-0 flex-col rounded-xl border border-em-line bg-white lg:h-full lg:flex-1">
      <div className="flex items-center gap-1 overflow-x-auto border-b border-em-line px-3 py-2">
        {tabs.map((tab, i) => {
          const p = progress[i];
          const complete = p.total > 0 && p.done === p.total;
          const label =
            (SECTION_LABELS as Record<string, string>)[tab] ??
            master.custom_sections.find((cs) => cs.key === tab)?.heading ??
            tab;
          return (
            <button
              key={tab}
              type="button"
              onClick={() => onChangeSection(tab)}
              className={cn(
                "shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors",
                tab === activeSection ? "bg-em-accent text-paper" : "text-ink/60 hover:bg-em-soft"
              )}
            >
              {complete && "✓ "}
              {label} {p.done}/{p.total}
            </button>
          );
        })}
        <button
          type="button"
          onClick={() => {
            const key = slugSectionId("SECTION", usedSectionKeys(master));
            onChange({
              ...master,
              custom_sections: [...master.custom_sections, { key, heading: "New section", entries: [] }],
            });
            onChangeSection(key);
          }}
          className="shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold whitespace-nowrap text-ink/40 hover:bg-em-soft hover:text-ink"
        >
          + Add section
        </button>
      </div>

      <div className="flex items-baseline justify-between px-4 pt-3">
        <p className="text-xs text-em-muted">
          {entryCount} entr{entryCount === 1 ? "y" : "ies"} · {active.total} fact
          {active.total === 1 ? "" : "s"}
        </p>
        <p className="font-mono text-[11px] text-em-faint">
          section {sectionIndex + 1} of {tabs.length}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        {activeSection === "EDUCATION" && <EducationPanel {...sectionProps} />}
        {activeSection === "EXPERIENCE" && <ExperiencePanel {...sectionProps} />}
        {activeSection === "PROJECTS" && <ProjectPanel {...sectionProps} />}
        {activeSection === "TECHNICAL SKILLS" && <SkillsPanel {...sectionProps} />}
        {customSection && (
          <CustomSectionPanel
            {...sectionProps}
            sectionKey={customSection.key}
            onBeforeRemove={() => {
              const idx = tabs.indexOf(customSection.key);
              onChangeSection(tabs[idx - 1] ?? tabs.find((t) => t !== customSection.key) ?? "EDUCATION");
            }}
          />
        )}
      </div>

      <div className="flex flex-col gap-2 border-t border-em-line px-4 py-3">
        <div className="flex flex-wrap gap-1.5">
          {(Object.keys(FILTER_LABELS) as Filter[]).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[11px] font-semibold transition-colors",
                filter === f
                  ? "border-em-accent bg-em-accent text-paper"
                  : "border-em-softb text-ink/60 hover:border-ink"
              )}
            >
              {FILTER_LABELS[f]}
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => onConfirmMany(active.keys, true)}>
              Confirm all in section
            </Button>
            <Button variant="ghost" onClick={() => onConfirmMany(active.keys, false)}>
              Unconfirm section
            </Button>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              disabled={sectionIndex === 0}
              onClick={() => onChangeSection(tabs[sectionIndex - 1])}
            >
              ‹ previous
            </Button>
            <Button
              variant="ghost"
              disabled={sectionIndex === tabs.length - 1}
              onClick={() => onChangeSection(tabs[sectionIndex + 1])}
            >
              next ›
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
