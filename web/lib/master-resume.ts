import type { MasterResume } from "@/lib/types";

// Mirrors core/pipeline.py's id assignment so facts and sections added in the
// browser satisfy the same <ENTITY>-<NN> contract the API will validate.

export function slugSectionId(label: string, taken: Set<string>): string {
  const base = (label.replace(/[^A-Za-z0-9]/g, "").toUpperCase() || "SEC").slice(0, 4);
  let id = base;
  let suffix = 2;
  while (taken.has(id)) {
    id = `${base}${suffix}`;
    suffix += 1;
  }
  taken.add(id);
  return id;
}

export function nextFactId(sectionId: string, existingIds: string[]): string {
  const used = new Set(
    existingIds
      .filter((id) => id.startsWith(`${sectionId}-`))
      .map((id) => Number(id.slice(sectionId.length + 1)))
  );
  let n = 1;
  while (used.has(n)) n += 1;
  return `${sectionId}-${String(n).padStart(2, "0")}`;
}

export function emptyMasterResume(): MasterResume {
  return {
    name: "",
    email: "",
    phone: "",
    links: [],
    education: [],
    experiences: [],
    projects: [],
    skills: {},
    custom_sections: [],
  };
}
