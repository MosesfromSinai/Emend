"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type DragEvent } from "react";

import {
  ConfirmPill,
  SectionPanel,
  SECTION_HEADINGS,
  allRowKeys,
} from "@/components/confirm/section-panel";
import { ParseError } from "@/components/parse-error";
import { ResumePaper, masterToSections } from "@/components/resume-paper";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  MAX_PDF_BYTES,
  MAX_TEXT_CHARS,
  getMaster,
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
  const [activeSection, setActiveSection] = useState<string>("EDUCATION");
  const resumePaperRef = useRef<HTMLDivElement>(null);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  // the error object, not a flattened string: ParseError decides what of it
  // a person should see, and keeps the raw text behind a toggle
  const [error, setError] = useState<unknown>(null);
  // client-side file checks, kept separate from `error` -- these never came
  // from the api, so ParseError's api-error-shaped messaging doesn't apply
  const [fileError, setFileError] = useState<string | null>(null);

  // Reopening /app via in-app back-navigation (e.g. the "back to confirm"
  // link from Tailor) shouldn't force a full re-paste when a resume was
  // already confirmed this visit -- load it straight into an editable
  // confirm view instead. But a genuinely fresh visit (new tab, or this
  // tab reopened after being closed) should start clean at paste, not
  // silently reload whatever was saved hours or days earlier -- sessionStorage
  // (cleared when the tab closes, unlike the year-long session cookie) is
  // what tells those two cases apart.
  useEffect(() => {
    const visitedThisTab = sessionStorage.getItem("emend_app_visited");
    sessionStorage.setItem("emend_app_visited", "1");
    if (!visitedThisTab) return;

    let cancelled = false;
    getMaster()
      .then((saved) => {
        if (cancelled) return;
        setMaster(saved);
        setConfirmed(new Set(allRowKeys(saved)));
        setStep("confirm");
        router.replace("/app?step=confirm");
      })
      .catch(() => {
        // no saved master (or a transient fetch error) -- just stay on paste
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function extractFacts(source: string) {
    setBusyPaste(true);
    setError(null);
    try {
      setMaster(await importResume(source));
      setConfirmed(new Set());
      setStep("confirm");
      router.replace("/app?step=confirm");
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
      setConfirmed(new Set());
      setStep("confirm");
      router.replace("/app?step=confirm");
    } catch (e) {
      setError(e);
    } finally {
      setBusyPdf(false);
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    if (busyPaste || busyPdf) return;
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

  // Auto-advance (section-panel.tsx) moves activeSection once every fact in
  // a section is confirmed -- follow it here so the resume side jumps to
  // the new section too, instead of leaving the user staring at the old one.
  useEffect(() => {
    const container = resumePaperRef.current;
    if (!container) return;
    const target = container.querySelector<HTMLElement>(
      `[data-section-heading="${activeSection}"]`,
    );
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [activeSection]);

  function sectionForKey(key: string): string | null {
    if (!master) return null;
    for (const section of masterToSections(master)) {
      if (section.blocks.some((b) => b.rows.some((r) => r.key === key))) {
        // matches SectionPanel's own tab identity: the fixed four are
        // identified by heading text, a custom section by its stable key
        // (which survives a rename, unlike its heading)
        return (SECTION_HEADINGS as readonly string[]).includes(section.heading)
          ? section.heading
          : section.key;
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
      // h-full, not a vh-minus-N guess: <main> in layout.tsx is now the sole
      // scroll container with a definite flex-1 height. The progress/actions
      // bar moved from a fixed bottom overlay to this compact top-right
      // block, so nothing reserves bottom space anymore -- the panels below
      // get the full remaining height.
      <div className="flex h-full flex-col gap-4">
        <div className="flex shrink-0 items-start justify-between gap-4">
          <div>
            <h1 className="font-serif text-2xl font-semibold">Did we get this right?</h1>
            <p className="mt-1 text-sm text-ink/70">
              These facts are the only material Emend will ever write from. Fix
              anything that&apos;s off before confirming. You can also add a new
              entry or delete one you don&apos;t want, in any section.
            </p>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                onClick={() => {
                  setStep("paste");
                  router.replace("/app");
                }}
                disabled={busySave}
              >
                Back
              </Button>
              <button
                type="button"
                onClick={() => (allConfirmed ? confirm() : setShowLeaveModal(true))}
                disabled={busySave}
                className={cn(
                  "rounded-lg px-4 py-2 text-sm font-medium text-paper shadow-[0_2px_10px_rgba(138,58,48,.35)] transition-colors disabled:cursor-not-allowed disabled:shadow-none",
                  allConfirmed
                    ? "bg-em-accent hover:bg-em-deep"
                    : "bg-em-accent/35 hover:bg-em-accent/45"
                )}
              >
                {busySave ? "Saving…" : "Continue to tailoring →"}
              </button>
            </div>
            <div className="w-44">
              <div className="h-1 w-full overflow-hidden rounded-full bg-em-line-2">
                <div
                  className="h-full bg-em-ok-fg transition-all"
                  style={{ width: `${allKeys.length ? (doneCount / allKeys.length) * 100 : 0}%` }}
                />
              </div>
              <p className="mt-1 text-right text-xs text-em-muted">
                {doneCount} of {allKeys.length} facts confirmed
              </p>
            </div>
          </div>
        </div>
        <ParseError error={error} />

        {/* flex, not grid: an auto-sized grid row sizes to its tallest
            child's own content height, not to this container's -- with
            flexbox, stretch correctly fills the definite height above
            instead of growing past it and defeating every overflow-y-auto
            below. lg:flex-[1.35]/[1] approximates the old 1.35fr/1fr split. */}
        <div className="flex min-h-0 flex-1 flex-col gap-5 lg:flex-row">
          <div
            ref={resumePaperRef}
            className="min-h-0 overflow-y-auto rounded-xl border border-em-line bg-white p-6 lg:h-full lg:flex-[1.35]"
          >
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
          facts and format it in LaTeX. Nothing is saved until you confirm.
        </p>
        <p className="mt-1 text-xs text-em-muted">
          Don&apos;t have a job posting yet? That&apos;s fine, you can format
          and edit your resume without tailoring to anything.
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
              if (!(busyPaste || busyPdf)) setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={cn(
              "flex flex-1 flex-col items-center justify-center rounded-xl border-[1.5px] border-dashed p-5 text-center transition-colors",
              (busyPaste || busyPdf) && "pointer-events-none opacity-60",
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
                <span className="text-em-accent">3.</span> We tailor and format a PDF from those
                facts only
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
