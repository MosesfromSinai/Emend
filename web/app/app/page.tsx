"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

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

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("paste");
  const [text, setText] = useState("");
  const [master, setMaster] = useState<MasterResume | null>(null);
  // split so uploading a PDF doesn't gray out the paste side and vice versa
  const [busyPaste, setBusyPaste] = useState(false);
  const [busyPdf, setBusyPdf] = useState(false);
  const [busySave, setBusySave] = useState(false);
  // the error object, not a flattened string: ParseError decides what of it
  // a person should see, and keeps the raw text behind a toggle
  const [error, setError] = useState<unknown>(null);
  // client-side file checks, kept separate from `error` -- these never came
  // from the api, so ParseError's api-error-shaped messaging doesn't apply
  const [fileError, setFileError] = useState<string | null>(null);

  async function extractFacts() {
    setBusyPaste(true);
    setError(null);
    try {
      setMaster(await importResume(text));
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
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, MAX_TEXT_CHARS))}
        rows={14}
        placeholder="Paste your resume here…"
      />
      <div className="flex items-center justify-between">
        <Button onClick={extractFacts} disabled={busyPaste || busyPdf || text.trim().length === 0}>
          {busyPaste ? "Extracting…" : "Extract my facts →"}
        </Button>
        {text.length > MAX_TEXT_CHARS * 0.9 && (
          <span className="font-mono text-xs text-ink/50">
            {text.length.toLocaleString()} / {MAX_TEXT_CHARS.toLocaleString()}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 text-xs text-ink/50">
        <div className="h-px flex-1 bg-em-softb" />
        or
        <div className="h-px flex-1 bg-em-softb" />
      </div>
      <label className="flex cursor-pointer items-center justify-center rounded-lg border-[1.5px] border-dashed border-em-softb bg-white px-5.5 py-3 text-[15px] font-semibold text-ink hover:border-ink">
        {busyPdf ? "Extracting…" : "Upload a PDF instead"}
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
  );
}
