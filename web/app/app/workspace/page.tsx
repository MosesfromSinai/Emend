"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, MAX_TEXT_CHARS, createApplication } from "@/lib/api";

export default function WorkspacePage() {
  const router = useRouter();
  const [jdText, setJdText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start(mode: "refactor" | "tailor") {
    setBusy(true);
    setError(null);
    try {
      const { id } = await createApplication(mode === "tailor" ? jdText : undefined);
      router.push(`/app/applications/${id}`);
    } catch (e) {
      if (e instanceof ApiError && e.code === "no_master_resume") {
        router.push("/app");
        return;
      }
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {error && <p className="text-sm text-red-700">{error}</p>}

      <section className="rounded-lg border border-em-softb p-5">
        <h2 className="mb-1 font-serif text-xl font-semibold">Refactor</h2>
        <p className="mb-4 text-sm text-ink/70">
          No job posting needed — typeset your confirmed resume as-is.
        </p>
        <Button onClick={() => start("refactor")} disabled={busy}>
          Refactor my resume
        </Button>
      </section>

      <section className="rounded-lg border border-em-softb p-5">
        <h2 className="mb-1 font-serif text-xl font-semibold">Tailor to a posting</h2>
        <p className="mb-4 text-sm text-ink/70">
          Paste a job description. Emend grounds every rewrite in the facts you
          confirmed — gaps are left as gaps, never invented.
        </p>
        <Textarea
          value={jdText}
          onChange={(e) => setJdText(e.target.value.slice(0, MAX_TEXT_CHARS))}
          rows={10}
          placeholder="Paste the job description here…"
          className="mb-3"
        />
        <Button
          onClick={() => start("tailor")}
          disabled={busy || jdText.trim().length === 0}
        >
          Tailor my resume →
        </Button>
      </section>
    </div>
  );
}
