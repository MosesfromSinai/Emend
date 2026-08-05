"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { KeywordChips } from "@/components/keyword-chips";
import { MatchScoreRing } from "@/components/match-score-ring";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, MAX_TEXT_CHARS, createApplication, previewJd } from "@/lib/api";
import type { JdPreview } from "@/lib/types";
import { cn } from "@/lib/utils";

type Mode = "tailor" | "refactor";

const SAMPLE_POSTING = `Backend Engineer — Nimbus Logistics

We're looking for a Backend Engineer to join our platform team.

Responsibilities:
- Build and maintain REST APIs in Python (FastAPI or similar)
- Design PostgreSQL schemas and write migrations
- Containerize services with Docker and support CI/CD pipelines
- Collaborate with frontend engineers building React interfaces

Requirements:
- 2+ years of experience with Python backend development
- Experience with relational databases (PostgreSQL preferred)
- Familiarity with Docker and cloud deployment
- Strong communication and code review habits`;

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
    // A slow request for a stale/partial input (e.g. a URL fetch mid-paste)
    // can resolve after a faster later one -- `stale` blocks it from
    // clobbering the current result once a newer effect run has started.
    let stale = false;
    const text = jdText.trim();
    const url = jdUrl.trim();
    const timer = setTimeout(async () => {
      if (mode !== "tailor" || (!text && !url)) {
        if (!stale) {
          setPreview(null);
          setPreviewError(null);
          setPreviewBusy(false);
        }
        return;
      }
      if (!stale) setPreviewBusy(true);
      try {
        const result = await previewJd(text ? { jdText: text } : { jdUrl: url });
        if (!stale) {
          setPreview(result);
          setPreviewError(null);
        }
      } catch (e) {
        if (!stale) {
          setPreview(null);
          setPreviewError(e instanceof ApiError ? e.message : "Couldn't score that posting.");
        }
      } finally {
        if (!stale) setPreviewBusy(false);
      }
    }, 500);
    return () => {
      stale = true;
      clearTimeout(timer);
    };
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

      <SegmentedControl
        value={mode}
        onChange={setMode}
        options={[
          { value: "tailor", label: "Tailor to a posting" },
          { value: "refactor", label: "Just typeset it" },
        ]}
      />

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
        <section className="grid grid-cols-1 gap-5 lg:grid-cols-[1.25fr_1fr]">
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
              className="mb-3 min-h-75"
              disabled={jdUrl.trim().length > 0}
            />
            <div className="mb-3 flex items-center gap-3 text-xs text-ink/50">
              <div className="h-px flex-1 bg-em-softb" />
              or
              <div className="h-px flex-1 bg-em-softb" />
            </div>
            <div className="mb-4 flex items-center gap-3">
              <Input
                type="url"
                value={jdUrl}
                onChange={(e) => {
                  setJdUrl(e.target.value);
                  if (e.target.value) setJdText("");
                }}
                placeholder="Paste a link to the posting instead…"
                disabled={jdText.trim().length > 0}
                className="flex-1"
              />
              <button
                type="button"
                onClick={() => {
                  setJdUrl("");
                  setJdText(SAMPLE_POSTING);
                }}
                className="shrink-0 text-sm font-medium text-em-accent hover:text-em-deep"
              >
                Use a sample posting
              </button>
            </div>
            <Button
              onClick={start}
              disabled={busy || (jdText.trim().length === 0 && jdUrl.trim().length === 0)}
            >
              {busy ? "Starting…" : "Tailor my resume →"}
            </Button>
          </div>

          <div
            className={cn(
              "rounded-xl border border-em-softb p-5",
              preview || previewError || previewBusy ? "bg-white" : "bg-em-soft"
            )}
          >
            {preview ? (
              <div className="flex flex-col gap-4">
                <p className="text-sm text-ink/70">
                  We compare a posting against your confirmed facts, then reorder
                  and reframe what you already have. Nothing new gets added.
                </p>
                <MatchScoreRing
                  score={preview.score}
                  missingCount={preview.missing_keywords.length}
                />
                <div>
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink/50">
                    Asked for in the posting · green means you already have it
                  </p>
                  <KeywordChips
                    matched={preview.matched_keywords}
                    missing={preview.missing_keywords}
                  />
                </div>
              </div>
            ) : previewError ? (
              <p className="text-sm text-red-700">{previewError}</p>
            ) : previewBusy ? (
              <p className="text-sm text-ink/60">Scoring against your resume…</p>
            ) : (
              <div>
                <h3 className="font-serif text-lg font-semibold">
                  Your compatibility score appears here
                </h3>
                <p className="mt-2 text-sm text-ink/70">
                  Paste a posting on the left. We pull out what it asks for,
                  measure it against your confirmed facts, and show you the
                  overlap. The score is a read on fit, not a target to write
                  toward.
                </p>
                <p className="mt-4 border-t border-em-softb pt-4 text-[11px] font-semibold uppercase tracking-wide text-ink/50">
                  What tailoring actually changes
                </p>
                <ul className="mt-2 flex flex-col gap-1.5 text-sm text-ink/70">
                  <li>Reorders your skills so the ones they asked for read first.</li>
                  <li>Leads each role with the bullets closest to the posting.</li>
                  <li>Matches their vocabulary for work you actually did.</li>
                  <li>Leaves every gap as a gap.</li>
                </ul>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
