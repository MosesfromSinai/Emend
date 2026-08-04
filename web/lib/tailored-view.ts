import type {
  BulletSelection,
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
  selections: Record<string, BulletSelection>
): MasterResume {
  if (!tailored) return master;

  const expById = new Map(master.experiences.map((e) => [e.id, e]));
  const projById = new Map(master.projects.map((p) => [p.id, p]));

  const experiences = tailored.experiences.flatMap((section) => {
    const src = expById.get(section.ref_id);
    if (!src) return [];
    return [
      {
        ...src,
        facts: section.bullets.map((b) => ({
          id: b.source_fact_ids[0],
          text: resolveVariantText(b, selections[b.source_fact_ids[0]]),
        })),
      },
    ];
  });

  const projects = tailored.projects.flatMap((section) => {
    const src = projById.get(section.ref_id);
    if (!src) return [];
    return [
      {
        ...src,
        facts: section.bullets.map((b) => ({
          id: b.source_fact_ids[0],
          text: resolveVariantText(b, selections[b.source_fact_ids[0]]),
        })),
      },
    ];
  });

  return { ...master, experiences, projects, skills: tailored.skills ?? master.skills };
}
