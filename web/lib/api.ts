import type {
  ApplicationListItem,
  ApplicationOut,
  BulletSelection,
  FactOrder,
  JdPreview,
  MasterResume,
  VersionOut,
} from "@/lib/types";

function wireSelections(selections: Record<string, BulletSelection>) {
  const wire: Record<string, { variant_idx?: number; custom_text?: string }> = {};
  for (const [factId, sel] of Object.entries(selections)) {
    wire[factId] = { variant_idx: sel.variantIdx, custom_text: sel.customText };
  }
  return wire;
}

// Compose sets this to http://localhost:8000; Vercel sets it to the Railway URL.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// mirrors api/config.py's MAX_TEXT_CHARS default — keeps us from bothering
// the server with a paste we already know it'll 422 on
export const MAX_TEXT_CHARS = 50000;

// mirrors core/extract.py's MAX_PDF_BYTES
export const MAX_PDF_BYTES = 5 * 1024 * 1024;

export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // FormData needs the browser to set its own Content-Type (with the
  // multipart boundary) -- forcing application/json here would break the
  // PDF upload path silently.
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include", // the session cookie is httpOnly; the browser sends it
    headers: isFormData ? init?.headers : { "Content-Type": "application/json", ...init?.headers },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const error = body?.error;
    throw new ApiError(
      res.status,
      error?.code ?? "unknown_error",
      error?.message ?? res.statusText,
      error?.details
    );
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function importResume(text: string): Promise<MasterResume> {
  return apiFetch("/resumes/import", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function importResumeFromFile(file: File): Promise<MasterResume> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch("/resumes/import", { method: "POST", body: form });
}

export function saveMaster(master: MasterResume): Promise<MasterResume> {
  return apiFetch("/resumes/master", {
    method: "PUT",
    body: JSON.stringify(master),
  });
}

export function getMaster(): Promise<MasterResume> {
  return apiFetch("/resumes/master");
}

// jdText and jdUrl are mutually exclusive — the api 422s if both are set.
export function createApplication(options?: {
  jdText?: string;
  jdUrl?: string;
  polish?: boolean;
}): Promise<{ id: string }> {
  return apiFetch("/applications", {
    method: "POST",
    body: JSON.stringify({
      jd_text: options?.jdText ?? null,
      jd_url: options?.jdUrl ?? null,
      polish: options?.polish ?? false,
    }),
  });
}

// jdText and jdUrl are mutually exclusive — exactly one is required.
export function previewJd(options: { jdText?: string; jdUrl?: string }): Promise<JdPreview> {
  return apiFetch("/jd/preview", {
    method: "POST",
    body: JSON.stringify({
      jd_text: options.jdText ?? null,
      jd_url: options.jdUrl ?? null,
    }),
  });
}

export function getApplication(id: string): Promise<ApplicationOut> {
  return apiFetch(`/applications/${id}`);
}

export interface RenderOptions {
  selections?: Record<string, BulletSelection>;
  factOrder?: FactOrder;
  experienceOrder?: string[];
  projectOrder?: string[];
  sectionOrder?: string[];
  excludedFacts?: string[];
  excludedExperiences?: string[];
  excludedProjects?: string[];
  textOverrides?: Record<string, string>;
}

function renderBody(opts: RenderOptions) {
  return {
    selections: wireSelections(opts.selections ?? {}),
    fact_order: opts.factOrder ?? {},
    experience_order: opts.experienceOrder?.length ? opts.experienceOrder : null,
    project_order: opts.projectOrder?.length ? opts.projectOrder : null,
    section_order: opts.sectionOrder?.length ? opts.sectionOrder : null,
    excluded_facts: opts.excludedFacts ?? [],
    excluded_experiences: opts.excludedExperiences ?? [],
    excluded_projects: opts.excludedProjects ?? [],
    text_overrides: opts.textOverrides ?? {},
  };
}

export function previewApplication(id: string, opts: RenderOptions): Promise<{ tex: string }> {
  return apiFetch(`/applications/${id}/preview`, {
    method: "POST",
    body: JSON.stringify(renderBody(opts)),
  });
}

export function finalizeApplication(id: string, opts: RenderOptions): Promise<VersionOut> {
  return apiFetch(`/applications/${id}/finalize`, {
    method: "POST",
    body: JSON.stringify(renderBody(opts)),
  });
}

export function listApplications(): Promise<ApplicationListItem[]> {
  return apiFetch("/applications");
}

// Permanently deletes the confirmed master resume, every application and
// its rendered PDF, and the session itself -- irreversible, no undo.
export function deleteMyData(): Promise<void> {
  return apiFetch("/account", { method: "DELETE" });
}

// pdf_url / tex_url from the API are already absolute paths like
// "/artifacts/<id>.pdf" — just point them at the api origin.
export function artifactUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
