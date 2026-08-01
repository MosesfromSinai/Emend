import type {
  ApplicationListItem,
  ApplicationOut,
  MasterResume,
} from "@/lib/types";

// Compose sets this to http://localhost:8000; Vercel sets it to the Fly URL.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include", // the session cookie is httpOnly; the browser sends it
    headers: { "Content-Type": "application/json", ...init?.headers },
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

export function saveMaster(master: MasterResume): Promise<MasterResume> {
  return apiFetch("/resumes/master", {
    method: "PUT",
    body: JSON.stringify(master),
  });
}

export function getMaster(): Promise<MasterResume> {
  return apiFetch("/resumes/master");
}

export function createApplication(jdText?: string): Promise<{ id: string }> {
  return apiFetch("/applications", {
    method: "POST",
    body: JSON.stringify({ jd_text: jdText ?? null }),
  });
}

export function getApplication(id: string): Promise<ApplicationOut> {
  return apiFetch(`/applications/${id}`);
}

export function listApplications(): Promise<ApplicationListItem[]> {
  return apiFetch("/applications");
}

// pdf_url / tex_url from the API are already absolute paths like
// "/artifacts/<id>.pdf" — just point them at the api origin.
export function artifactUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
