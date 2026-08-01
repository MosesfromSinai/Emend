"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { MasterResumeEditor } from "@/components/master-resume-editor";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, MAX_TEXT_CHARS, importResume, saveMaster } from "@/lib/api";
import type { MasterResume } from "@/lib/types";

type Step = "paste" | "confirm";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("paste");
  const [text, setText] = useState("");
  const [master, setMaster] = useState<MasterResume | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function extractFacts() {
    setBusy(true);
    setError(null);
    try {
      setMaster(await importResume(text));
      setStep("confirm");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!master) return;
    setBusy(true);
    setError(null);
    try {
      await saveMaster(master);
      router.push("/app/workspace");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
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
        {error && <p className="text-sm text-red-700">{error}</p>}
        <MasterResumeEditor master={master} onChange={setMaster} />
        <div className="flex items-center gap-3">
          <Button onClick={confirm} disabled={busy}>
            {busy ? "Saving…" : "Looks right — confirm"}
          </Button>
          <Button variant="ghost" onClick={() => setStep("paste")} disabled={busy}>
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
          Paste it as plain text — we&apos;ll pull out the facts and typeset it
          in LaTeX. Nothing is saved until you confirm.
        </p>
      </div>
      {error && <p className="text-sm text-red-700">{error}</p>}
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, MAX_TEXT_CHARS))}
        rows={14}
        placeholder="Paste your resume here…"
      />
      <div className="flex items-center justify-between">
        <Button onClick={extractFacts} disabled={busy || text.trim().length === 0}>
          {busy ? "Extracting…" : "Extract my facts →"}
        </Button>
        {text.length > MAX_TEXT_CHARS * 0.9 && (
          <span className="font-mono text-xs text-ink/50">
            {text.length.toLocaleString()} / {MAX_TEXT_CHARS.toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
}
