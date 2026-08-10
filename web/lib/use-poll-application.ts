"use client";

import { useEffect, useState } from "react";

import { ApiError, getApplication } from "@/lib/api";
import type { ApplicationOut } from "@/lib/types";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES = new Set(["done", "failed"]);

export function usePollApplication(id: string) {
  const [application, setApplication] = useState<ApplicationOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Bumped to re-enter the effect below after the poll loop has already
  // stopped at a terminal status -- e.g. right after triggering the
  // AI-polish upgrade on an already-`done` application, which flips it back
  // to `queued` server-side but wouldn't otherwise be noticed until the
  // caller re-mounts.
  const [generation, setGeneration] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const app = await getApplication(id);
        if (cancelled) return;
        setApplication(app);
        if (!TERMINAL_STATUSES.has(app.status)) {
          timer = setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Network error.");
      }
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [id, generation]);

  return { application, error, restartPolling: () => setGeneration((g) => g + 1) };
}
