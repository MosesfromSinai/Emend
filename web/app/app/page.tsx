"use client";

import { useRouter } from "next/navigation";
import { useState, type DragEvent } from "react";

import {
  ConfirmPill,
  SectionPanel,
  SECTION_HEADINGS,
  allRowKeys,
  type SectionHeading,
} from "@/components/confirm/section-panel";
import { ParseError } from "@/components/parse-error";
import { ResumePaper, masterToSections } from "@/components/resume-paper";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  MAX_PDF_BYTES,
  MAX_TEXT_CHARS,
  importResume,
  importResumeFromFile,
  saveMaster,
} from "@/lib/api";
import { cn } from "@/lib/utils";
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
  const [dragOver, setDragOver] = useState(false);
  // which facts a person has checked off -- ephemeral, never persisted; the
  // only real save is the PUT /resumes/master on confirm
  const [confirmed, setConfirmed] = useState<Set<string>>(new Set());
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<SectionHeading>("EDUCATION");
  const [showLeaveModal, setShowLeaveModal] = useState(false);
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
      setFileError("That PDF is too large. Please upload one under 5 MB.");
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

  function toggleConfirm(key: string) {
    setConfirmed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function confirmMany(keys: string[], value: boolean) {
    setConfirmed((prev) => {
      const next = new Set(prev);
      for (const key of keys) {
        if (value) next.add(key);
        else next.delete(key);
      }
      return next;
    });
  }

  function sectionForKey(key: string): SectionHeading | null {
    if (!master) return null;
    for (const section of masterToSections(master)) {
      if (section.blocks.some((b) => b.rows.some((r) => r.key === key))) {
        return section.heading as SectionHeading;
      }
    }
    return null;
  }

  if (step === "confirm" && master) {
    const contact = [master.email, master.phone, ...master.links].filter(Boolean).join(" | ");
    const allKeys = allRowKeys(master);
    const doneCount = allKeys.filter((k) => confirmed.has(k)).length;
    const allConfirmed = allKeys.length > 0 && doneCount === allKeys.length;
    const remaining = allKeys.length - doneCount;

    return (
      <div className="flex flex-col gap-4 pb-28">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Did we get this right?</h1>
          <p className="mt-1 text-sm text-ink/70">
            These facts are the only material Emend will ever write from. Fix
            anything that&apos;s off before confirming.
          </p>
        </div>
        <ParseError error={error} />

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.35fr_1fr]">
          <div className="sticky top-20 h-[calc(100vh-110px)] self-start overflow-y-auto rounded-xl border border-em-line bg-white p-6">
            <ResumePaper
              master={master}
              name={master.name}
              contact={contact}
              hoveredKey={hoveredKey}
              onHoverRow={setHoveredKey}
              onClickRow={(row) => {
                const section = sectionForKey(row.key);
                if (section) setActiveSection(section);
              }}
              activeSectionHeading={activeSection}
              confirmedKeys={confirmed}
              renderRowExtra={(row) => (
                <span onClick={(e) => e.stopPropagation()}>
                  <ConfirmPill
                    confirmed={confirmed.has(row.key)}
                    onToggle={() => toggleConfirm(row.key)}
                  />
                </span>
              )}
            />
          </div>

          <SectionPanel
            master={master}
            onChange={setMaster}
            confirmed={confirmed}
            onToggleConfirm={toggleConfirm}
            onConfirmMany={confirmMany}
            activeSection={activeSection}
            onChangeSection={setActiveSection}
            hoveredKey={hoveredKey}
            onHoverRow={setHoveredKey}
          />
        </div>

        <div className="fixed inset-x-0 bottom-0 z-30 border-t border-em-line bg-paper/95 backdrop-blur-sm">
          <div className="mx-auto flex max-w-390 items-center gap-4 px-7 py-3">
            <div className="flex-1">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-em-line-2">
                <div
                  className="h-full bg-em-bright transition-all"
                  style={{ width: `${allKeys.length ? (doneCount / allKeys.length) * 100 : 0}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-em-muted">
                {doneCount} of {allKeys.length} facts confirmed
              </p>
            </div>
            <Button variant="ghost" onClick={() => setStep("paste")} disabled={busySave}>
              Back
            </Button>
            <button
              type="button"
              onClick={() => (allConfirmed ? confirm() : setShowLeaveModal(true))}
              disabled={busySave}
              className={cn(
                "rounded-lg px-4 py-2 text-sm font-medium text-paper transition-colors disabled:cursor-not-allowed",
                allConfirmed
                  ? "bg-em-accent hover:bg-em-deep"
                  : "bg-em-accent/35 hover:bg-em-accent/45"
              )}
            >
              {busySave ? "Saving…" : "Continue to tailoring →"}
            </button>
          </div>
        </div>

        {showLeaveModal && (
          <div className="fixed inset-0 z-40 flex items-center justify-center bg-ink/40 px-4">
            <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
              <h2 className="font-serif text-lg font-semibold">Keep reviewing?</h2>
              <p className="mt-2 text-sm text-ink/70">
                {remaining} fact{remaining === 1 ? "" : "s"} still need confirmation. You can
                confirm the rest later, but nothing unconfirmed gets a second look.
              </p>
              <div className="mt-4 flex justify-end gap-3">
                <Button variant="ghost" onClick={() => setShowLeaveModal(false)}>
                  Keep reviewing
                </Button>
                <Button
                  onClick={() => {
                    setShowLeaveModal(false);
                    confirm();
                  }}
                >
                  Continue anyway
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="font-serif text-2xl font-semibold">Let&apos;s get your resume in.</h1>
        <p className="mt-1 text-sm text-ink/70">
          Paste it as plain text, or upload a PDF, and we&apos;ll pull out the
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

        <div className="flex h-full flex-col gap-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={cn(
              "flex flex-1 flex-col items-center justify-center rounded-xl border-[1.5px] border-dashed p-5 text-center transition-colors",
              dragOver ? "border-ink bg-em-soft/40" : "border-em-line-2 bg-white"
            )}
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

          <div className="rounded-xl border border-em-softb bg-em-soft px-4.5 py-4">
            <p className="text-xs font-semibold tracking-wide text-em-accent uppercase">
              What happens next
            </p>
            <ul className="mt-2 flex flex-col gap-1.5 text-[13px] text-ink">
              <li>
                <span className="text-em-accent">1.</span> We split your resume into individual
                facts
              </li>
              <li>
                <span className="text-em-accent">2.</span>{" "}You confirm what&apos;s accurate
              </li>
              <li>
                <span className="text-em-accent">3.</span> We tailor and typeset a PDF from those
                facts only
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
