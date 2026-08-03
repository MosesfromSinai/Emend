"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api";

/** What we say instead of whatever the parser actually complained about. */
const FRIENDLY_MESSAGES: Record<string, string> = {
  unstructurable_resume:
    "We couldn't read this resume cleanly. Try pasting it again straight from your document — plain text, one bullet per line.",
  payload_too_large: "That resume is longer than we can take in one go. Trim it down and try again.",
};
const FALLBACK_MESSAGE = "Something went wrong. Give it another try.";

function friendlyMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return FALLBACK_MESSAGE;
  return FRIENDLY_MESSAGES[error.code] ?? error.message ?? FALLBACK_MESSAGE;
}

/** The raw text, if there is any worth showing behind the toggle. */
function rawDetail(error: unknown): string | null {
  if (!(error instanceof ApiError)) {
    return error instanceof Error ? error.message : null;
  }
  // only worth a toggle when it says more than the friendly line already does
  return FRIENDLY_MESSAGES[error.code] && error.message ? error.message : null;
}

export function ParseError({ error }: { error: unknown }) {
  const [showDetails, setShowDetails] = useState(false);
  if (error == null) return null;

  const detail = rawDetail(error);

  return (
    <div
      role="alert"
      className="rounded-lg border border-red-200 bg-red-50/60 px-4 py-3 text-sm"
    >
      <p className="text-red-800">{friendlyMessage(error)}</p>
      {detail && (
        <>
          <button
            type="button"
            onClick={() => setShowDetails((open) => !open)}
            className="mt-2 text-xs text-red-700/80 underline hover:text-red-900"
          >
            {showDetails ? "Hide details" : "Show details"}
          </button>
          {showDetails && (
            <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded border border-red-200 bg-white/70 p-2 font-mono text-xs text-ink/70">
              {detail}
            </pre>
          )}
        </>
      )}
    </div>
  );
}
