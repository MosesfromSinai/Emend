import { excludeByKey, reorderByKey } from "@/lib/order";
import type {
  BulletSelection,
  FactOrder,
  MasterResume,
  TailoredBullet,
  TailoredResume,
} from "@/lib/types";

// Mirrors latex/render.py's _resolve_variant -- selections are keyed by a
// bullet's first source fact id, since Export's per-line picker treats a
// bullet as one unit regardless of how many facts it cites.
export function resolveVariantText(bullet: TailoredBullet, selection?: BulletSelection): string {
  if (!selection) return bullet.variants[0];
  if (selection.customText) return selection.customText;
  return bullet.variants[selection.variantIdx ?? 0];
}

// Mirrors latex/render.py's _ov -- a user's free-text edit for any
// non-fact-backed field, keyed by a stable path string.
function overrideText(overrides: Record<string, string>, key: string, fallback: string): string {
  return key in overrides ? overrides[key] : fallback;
}

// Same idea for comma-joined list fields (coursework, tech, skills items) --
// the override is one free-text blob matching how it already displays, split
// back into a list the same way ", ".join(...)/join(", ") would read it.
function overrideList(overrides: Record<string, string>, key: string, fallback: string[]): string[] {
  if (!(key in overrides)) return fallback;
  const text = overrides[key].trim();
  return text ? text.split(",").map((s) => s.trim()) : [];
}

export function tailoredBulletsByFactId(
  tailored: TailoredResume | null
): Map<string, TailoredBullet> {
  const map = new Map<string, TailoredBullet>();
  if (!tailored) return map;
  for (const section of [...tailored.experiences, ...tailored.projects]) {
    for (const bullet of section.bullets) {
      map.set(bullet.source_fact_ids[0], bullet);
    }
  }
  return map;
}

// Builds a MasterResume-shaped view for resume-paper.tsx to render: in
// tailor mode only the entries the tailor step selected show up, each with
// its tailored bullets (resolved to whichever variant/edit is selected)
// standing in for the master's facts -- structural fields (company, title,
// dates, tech) always come from master, never from the tailor.
export function tailoredToRenderResume(
  master: MasterResume,
  tailored: TailoredResume | null,
  selections: Record<string, BulletSelection>,
  factOrder: FactOrder = {},
  experienceOrder: string[] = [],
  projectOrder: string[] = [],
  excludedFacts: string[] = [],
  excludedExperiences: string[] = [],
  excludedProjects: string[] = []
): MasterResume {
  if (!tailored) return master;

  const expById = new Map(master.experiences.map((e) => [e.id, e]));
  const projById = new Map(master.projects.map((p) => [p.id, p]));

  const liveExperienceSections = excludeByKey(tailored.experiences, excludedExperiences, (s) => s.ref_id);
  const liveProjectSections = excludeByKey(tailored.projects, excludedProjects, (s) => s.ref_id);
  const orderedExperienceSections = reorderByKey(liveExperienceSections, experienceOrder, (s) => s.ref_id);
  const orderedProjectSections = reorderByKey(liveProjectSections, projectOrder, (s) => s.ref_id);

  const experiences = orderedExperienceSections.flatMap((section) => {
    const src = expById.get(section.ref_id);
    if (!src) return [];
    const liveBullets = excludeByKey(section.bullets, excludedFacts, (b) => b.source_fact_ids[0]);
    const bullets = reorderByKey(liveBullets, factOrder[section.ref_id], (b) => b.source_fact_ids[0]);
    return [
      {
        ...src,
        facts: bullets.map((b) => ({
          id: b.source_fact_ids[0],
          text: resolveVariantText(b, selections[b.source_fact_ids[0]]),
        })),
      },
    ];
  });

  const projects = orderedProjectSections.flatMap((section) => {
    const src = projById.get(section.ref_id);
    if (!src) return [];
    const liveBullets = excludeByKey(section.bullets, excludedFacts, (b) => b.source_fact_ids[0]);
    const bullets = reorderByKey(liveBullets, factOrder[section.ref_id], (b) => b.source_fact_ids[0]);
    return [
      {
        ...src,
        facts: bullets.map((b) => ({
          id: b.source_fact_ids[0],
          text: resolveVariantText(b, selections[b.source_fact_ids[0]]),
        })),
      },
    ];
  });

  return { ...master, experiences, projects, skills: tailored.skills ?? master.skills };
}
