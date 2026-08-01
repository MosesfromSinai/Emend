"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, listApplications } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";

// plain client fetch on mount, no polling needed here — this is a static
// list, the live status updates happen on the application detail page

const STATUS_LABEL: Record<string, string> = {
  queued: "Queued",
  running: "Running",
  done: "Done",
  failed: "Failed",
};

export default function HistoryPage() {
  const [applications, setApplications] = useState<ApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listApplications()
      .then(setApplications)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Network error."));
  }, []);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!applications) return <p className="text-sm text-ink/60">Loading…</p>;
  if (applications.length === 0) {
    return <p className="text-sm text-ink/60">No applications yet.</p>;
  }

  return (
    <ul className="flex flex-col divide-y divide-em-softb rounded-lg border border-em-softb">
      {applications.map((app) => (
        <li key={app.id}>
          <Link
            href={`/app/applications/${app.id}`}
            className="flex items-center justify-between px-4 py-3 hover:bg-em-soft/40"
          >
            <div>
              <p className="font-medium capitalize">{app.mode}</p>
              <p className="text-xs text-ink/60">
                {new Date(app.created_at).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {app.match_score !== null && (
                <span className="font-mono text-xs text-em-deep">
                  {Math.round(app.match_score * 100)}%
                </span>
              )}
              <span
                className={
                  "rounded-full px-2.5 py-1 text-xs font-medium " +
                  (app.status === "failed"
                    ? "bg-red-100 text-red-700"
                    : app.status === "done"
                      ? "bg-[#eef0e2] text-[#5a6a34]"
                      : "bg-em-soft text-em-deep")
                }
              >
                {STATUS_LABEL[app.status] ?? app.status}
              </span>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
