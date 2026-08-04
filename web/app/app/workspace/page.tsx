"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { KeywordChips } from "@/components/keyword-chips";
import { MatchScoreRing } from "@/components/match-score-ring";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, MAX_TEXT_CHARS, createApplication, previewJd } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { JdPreview } from "@/lib/types";

type Mode = "tailor" | "refactor";

export default function WorkspacePage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("tailor");
  const [jdText, setJdText] = useState("");
  const [jdUrl, setJdUrl] = useState("");
  const [preview, setPreview] = useState<JdPreview | null>(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const text = jdText.trim();
    const url = jdUrl.trim();
    const timer = setTimeout(async () => {
      if (mode !== "tailor" || (!text && !url)) {
        setPreview(null);
        setPreviewError(null);
        setPreviewBusy(false);
        return;
      }
      setPreviewBusy(true);
      try {
        const result = await previewJd(text ? { jdText: text } : { jdUrl: url });
        setPreview(result);
        setPreviewError(null);
      } catch (e) {
        setPreview(null);
        setPreviewError(e instanceof ApiError ? e.message : "Couldn't score that posting.");
      } finally {
        setPreviewBusy(false);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [mode, jdText, jdUrl]);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const { id } = await createApplication(
        mode === "tailor" ? { jdText: jdText || undefined, jdUrl: jdUrl || undefined } : undefined
      );
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
    <div className="flex flex-col gap-6">
      {error && <p className="text-sm text-red-700">{error}</p>}

      <div className="inline-flex w-fit rounded-full border border-em-line bg-white p-1">
        {(
          [
            { key: "tailor", label: "Tailor to a posting" },
            { key: "refactor", label: "Just typeset it" },
          ] as const
        ).map((option) => (
          <button
            key={option.key}
            type="button"
            onClick={() => setMode(option.key)}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
              mode === option.key ? "bg-ink text-paper" : "text-ink/60 hover:text-ink"
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {mode === "refactor" ? (
        <section className="rounded-xl border border-em-line bg-white p-5">
          <div className="mb-1 flex items-center gap-2">
            <h2 className="font-serif text-xl font-semibold">Just typeset it</h2>
            <span className="rounded-full bg-em-line-2 px-2.5 py-1 font-mono text-[11px] font-semibold text-em-muted-2">
              0 rewrites
            </span>
          </div>
          <p className="mb-4 text-sm text-ink/70">
            No job posting needed — typeset your confirmed resume as-is, word for word.
          </p>
          <Button onClick={start} disabled={busy}>
            {busy ? "Starting…" : "Typeset my resume →"}
          </Button>
        </section>
      ) : (
        <section className="grid grid-cols-1 gap-5 lg:grid-cols-[1.35fr_1fr]">
          <div className="rounded-xl border border-em-line bg-white p-5">
            <h2 className="mb-1 font-serif text-xl font-semibold">Tailor to a posting</h2>
            <p className="mb-4 text-sm text-ink/70">
              Paste a job description, or a link to one. Emend grounds every
              rewrite in the facts you confirmed — gaps are left as gaps, never
              invented.
            </p>
            <Textarea
              value={jdText}
              onChange={(e) => {
                setJdText(e.target.value.slice(0, MAX_TEXT_CHARS));
                if (e.target.value) setJdUrl("");
              }}
              rows={10}
              placeholder="Paste the job description here…"
              className="mb-3"
              disabled={jdUrl.trim().length > 0}
            />
            <div className="mb-3 flex items-center gap-3 text-xs text-ink/50">
              <div className="h-px flex-1 bg-em-softb" />
              or
              <div className="h-px flex-1 bg-em-softb" />
            </div>
            <Input
              type="url"
              value={jdUrl}
              onChange={(e) => {
                setJdUrl(e.target.value);
                if (e.target.value) setJdText("");
              }}
              placeholder="Paste a link to the posting instead…"
              className="mb-4"
              disabled={jdText.trim().length > 0}
            />
            <Button
              onClick={start}
              disabled={busy || (jdText.trim().length === 0 && jdUrl.trim().length === 0)}
            >
              {busy ? "Starting…" : "Tailor my resume →"}
            </Button>
          </div>

          <div className="rounded-xl bg-ink p-5 text-paper">
            {previewBusy && !preview && (
              <p className="text-sm text-paper/70">Scoring against your resume…</p>
            )}
            {!previewBusy && !preview && !previewError && (
              <p className="text-sm text-paper/60">
                Paste a posting to see your match score here.
              </p>
            )}
            {previewError && <p className="text-sm text-red-300">{previewError}</p>}
            {preview && (
              <div className="flex flex-col gap-4">
                <MatchScoreRing score={preview.score} dark />
                <KeywordChips
                  matched={preview.matched_keywords}
                  missing={preview.missing_keywords}
                />
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
