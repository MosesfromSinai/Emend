// Hand-written from core/schemas.py and api/schemas.py — the team contract.
// Field names and shapes must match exactly; see docs/integration-guide.md.

export interface Fact {
  id: string;
  text: string;
}

export interface Experience {
  id: string;
  company: string;
  title: string;
  location: string;
  start: string;
  end: string;
  facts: Fact[];
}

export interface Project {
  id: string;
  name: string;
  tech: string[];
  facts: Fact[];
}

export interface Education {
  school: string;
  degree: string;
  location: string;
  grad_date: string;
  coursework: string[];
}

// A user-named section for content outside Education/Experience/Projects/
// Skills ("Research Experience", "Certifications"). Never AI-tailored --
// an entry's facts always render as literal confirmed text, in every mode.
export interface CustomEntry {
  id: string;
  title: string;
  subtitle: string;
  location: string;
  start: string;
  end: string;
  facts: Fact[];
}

export interface CustomSection {
  key: string; // internal id for section_order/text_overrides, never shown to the user
  heading: string; // the user's own label, e.g. "Research Experience"
  entries: CustomEntry[];
}

export interface MasterResume {
  name: string;
  email: string;
  phone: string;
  links: string[];
  education: Education[];
  experiences: Experience[];
  projects: Project[];
  skills: Record<string, string[]>;
  custom_sections: CustomSection[];
}

export interface TailoredBullet {
  variants: string[];
  source_fact_ids: string[];
}

export interface TailoredSection {
  ref_id: string;
  bullets: TailoredBullet[];
}

export interface TailoredResume {
  summary_of_strategy: string;
  experiences: TailoredSection[];
  projects: TailoredSection[];
  skills: Record<string, string[]>;
}

export interface BulletVerdict {
  bullet: string;
  supported: boolean;
  reason: string;
  source_fact_ids: string[];
}

export interface Report {
  match_score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  grounding_ok: boolean;
  verdicts: BulletVerdict[];
}

export interface JdPreview {
  score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  resolved_jd_text: string;
}

export type ApplicationMode = "refactor" | "tailor" | "polish";
export type ApplicationStatus = "queued" | "running" | "done" | "failed";

// keyed by a bullet's first source_fact_id, mirrors api's BulletSelection
export interface BulletSelection {
  variantIdx?: number;
  customText?: string;
}

// keyed by an experience/project's own id -- the full ordered list of that
// entry's fact ids after the user's up/down moves, mirrors api's
// RenderRequest.fact_order
export type FactOrder = Record<string, string[]>;

export interface VersionOut {
  id: string;
  tex: string;
  report: Report | null;
  tailored: TailoredResume | null;
  // fact id -> text snapshot of the master resume as it was when this
  // version was generated -- see applications/[id]/page.tsx originalTextByFactId
  source_facts: Record<string, string>;
  pdf_url: string;
  tex_url: string;
  created_at: string;
}

export interface ApplicationOut {
  id: string;
  mode: ApplicationMode;
  status: ApplicationStatus;
  match_score: number | null;
  matched_keywords: string[] | null;
  missing_keywords: string[] | null;
  error: string | null;
  created_at: string;
  version: VersionOut | null;
  jd_source_url: string | null;
}

export interface ApplicationListItem {
  id: string;
  mode: ApplicationMode;
  status: ApplicationStatus;
  match_score: number | null;
  error: string | null;
  created_at: string;
}
