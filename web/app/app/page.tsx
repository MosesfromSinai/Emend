"use client";

import { useRouter } from "next/navigation";
import { useState, type DragEvent } from "react";

import { MasterResumeEditor } from "@/components/master-resume-editor";
import { ParseError } from "@/components/parse-error";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  MAX_PDF_BYTES,
  MAX_TEXT_CHARS,
  importResume,
  importResumeFromFile,
  saveMaster,
} from "@/lib/api";
import type { MasterResume } from "@/lib/types";

type Step = "paste" | "confirm";

const SAMPLE_RESUME = `Jordan Diaz
jordan.diaz@email.com | (555) 019-2231 | linkedin.com/in/jordandiaz

EDUCATION
University of Michigan — B.S. Computer Science, May 2022
Coursework: Data Structures, Operating Systems, Distributed Systems

EXPERIENCE
Backend Engineer, Nimbus Logistics — Ann Arbor, MI (Jun 2022 – Present)
- Rebuilt the shipment-tracking API on FastAPI, cutting p95 latency 40%.
- Migrated 12 cron jobs to an event-driven queue, removing 3 hours/week of manual reruns.
- Wrote the on-call runbook adopted by all 6 engineers on the team.

PROJECTS
Routewise (Python, PostgreSQL, Redis)
- Built a route-optimization service handling 10k+ requests/day.
- Added Redis caching that cut average response time from 800ms to 120ms.

TECHNICAL SKILLS
Languages: Python, TypeScript, SQL
Frameworks/Libraries: FastAPI, React, SQLAlchemy`;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("paste");
  const [text, setText] = useState("");
  const [master, setMaster] = useState<MasterResume | null>(null);
  // split so uploading a PDF doesn't gray out the paste side and vice versa
  const [busyPaste, setBusyPaste] = useState(false);
  const [busyPdf, setBusyPdf] = useState(false);
  const [busySave, setBusySave] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  // the error object, not a flattened string: ParseError decides what of it
  // a person should see, and keeps the raw text behind a toggle
  const [error, setError] = useState<unknown>(null);
  // client-side file checks, kept separate from `error` -- these never came
  // from the api, so ParseError's api-error-shaped messaging doesn't apply
  const [fileError, setFileError] = useState<string | null>(null);

  async function extractFacts(source: string) {
    setBusyPaste(true);
    setError(null);
    try {
      setMaster(await importResume(source));
      setStep("confirm");
    } catch (e) {
      setError(e);
    } finally {
      setBusyPaste(false);
    }
  }

  async function extractFromFile(file: File) {
    setFileError(null);
    if (file.type !== "application/pdf") {
      setFileError("That doesn't look like a PDF. Please upload a .pdf file.");
      return;
    }
    if (file.size > MAX_PDF_BYTES) {
      setFileError("That PDF is too large — please upload one under 5 MB.");
      return;
    }
    setBusyPdf(true);
    setError(null);
    try {
      setMaster(await importResumeFromFile(file));
      setStep("confirm");
    } catch (e) {
      setError(e);
    } finally {
      setBusyPdf(false);
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) extractFromFile(file);
  }

  async function confirm() {
    if (!master) return;
    setBusySave(true);
    setError(null);
    try {
      await saveMaster(master);
      router.push("/app/workspace");
    } catch (e) {
      setError(e);
    } finally {
      setBusySave(false);
    }
  }

  if (step === "confirm" && master) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Did we get this right?</h1>
          <p className="mt-1 text-sm text-ink/70">
            These facts are the only material Emend will ever write from. Fix
            anything that&apos;s off before confirming.
          </p>
        </div>
        <ParseError error={error} />
        <MasterResumeEditor master={master} onChange={setMaster} />
        <div className="flex items-center gap-3">
          <Button onClick={confirm} disabled={busySave}>
            {busySave ? "Saving…" : "Looks right — confirm"}
          </Button>
          <Button variant="ghost" onClick={() => setStep("paste")} disabled={busySave}>
            Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="font-serif text-2xl font-semibold">Let&apos;s get your resume in.</h1>
        <p className="mt-1 text-sm text-ink/70">
          Paste it as plain text, or upload a PDF — we&apos;ll pull out the
          facts and typeset it in LaTeX. Nothing is saved until you confirm.
        </p>
      </div>
      <ParseError error={error} />
      {fileError && <p className="text-sm text-red-700">{fileError}</p>}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.35fr_1fr]">
        <div className="overflow-hidden rounded-xl border border-em-line bg-white">
          <div className="border-b border-em-line bg-em-panel px-4.5 py-2.5 text-xs font-semibold tracking-wide text-em-muted-2 uppercase">
            Paste your resume
          </div>
          <div className="flex flex-col gap-3 p-4.5">
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value.slice(0, MAX_TEXT_CHARS))}
              rows={16}
              placeholder="Paste your resume here…"
            />
            <div className="flex items-center justify-between">
              <Button
                onClick={() => extractFacts(text)}
                disabled={busyPaste || busyPdf || text.trim().length === 0}
              >
                {busyPaste ? "Extracting…" : "Extract my facts →"}
              </Button>
              <span className="font-mono text-xs text-em-faint">
                {text.length.toLocaleString()} chars ·{" "}
                {(text.length === 0 ? 0 : text.split("\n").length).toLocaleString()} lines
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={
              "rounded-xl border-[1.5px] border-dashed p-5 text-center transition-colors " +
              (dragOver ? "border-ink bg-em-soft/40" : "border-em-line-2 bg-white")
            }
          >
            <p className="text-sm font-semibold text-ink">Drop a PDF here</p>
            <p className="mt-1 text-xs text-em-muted">or</p>
            <label className="mt-3 flex cursor-pointer items-center justify-center rounded-lg border-[1.5px] border-em-softb bg-white px-4 py-2.5 text-sm font-semibold text-ink hover:border-ink">
              {busyPdf ? "Extracting…" : "Browse for a PDF"}
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                disabled={busyPaste || busyPdf}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  e.target.value = ""; // allow re-selecting the same file after an error
                  if (file) extractFromFile(file);
                }}
              />
            </label>
          </div>

          <div className="rounded-xl bg-ink px-4.5 py-4 text-paper">
            <p className="text-xs font-semibold tracking-wide text-paper/60 uppercase">
              What happens next
            </p>
            <ul className="mt-2 flex flex-col gap-1.5 text-[13px] text-paper/85">
              <li>1. We split your resume into individual facts</li>
              <li>2. You confirm what&apos;s accurate</li>
              <li>3. We tailor and typeset a PDF from those facts only</li>
            </ul>
          </div>

          <Button
            variant="secondary"
            onClick={() => extractFacts(SAMPLE_RESUME)}
            disabled={busyPaste || busyPdf}
          >
            Use a sample resume
          </Button>
        </div>
      </div>
    </div>
  );
}
