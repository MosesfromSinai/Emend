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

export interface MasterResume {
  name: string;
  email: string;
  phone: string;
  links: string[];
  education: Education[];
  experiences: Experience[];
  projects: Project[];
  skills: Record<string, string[]>;
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

export type ApplicationMode = "refactor" | "tailor";
export type ApplicationStatus = "queued" | "running" | "done" | "failed";

export interface VersionOut {
  id: string;
  tex: string;
  report: Report | null;
  tailored: TailoredResume | null;
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
