"use client";

import { use, useEffect, useMemo, useState } from "react";

import { RewriteBar } from "@/components/export/rewrite-bar";
import { GroundedPill } from "@/components/grounded-pill";
import { KeywordChips } from "@/components/keyword-chips";
import { MatchScoreRing } from "@/components/match-score-ring";
import { ProvenancePanel } from "@/components/provenance-panel";
import { ResumePaper } from "@/components/resume-paper";
import { TexPane } from "@/components/tex-pane";
import { Button } from "@/components/ui/button";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { ApiError, artifactUrl, finalizeApplication, getMaster, previewApplication } from "@/lib/api";
import { tailoredBulletsByFactId, tailoredToRenderResume } from "@/lib/tailored-view";
import { usePollApplication } from "@/lib/use-poll-application";
import type { BulletSelection, FactOrder, MasterResume } from "@/lib/types";

const PREVIEW_DEBOUNCE_MS = 400;

type View = "resume" | "tex";

const VIEW_HINTS: Record<View, string> = {
  resume: "Click any line to swap in a different rewrite or your original.",
  tex: "Every generated line carries a % grounded receipt.",
};

export default function ApplicationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { application, error } = usePollApplication(id);
  const [master, setMaster] = useState<MasterResume | null>(null);
  const [selections, setSelections] = useState<Record<string, BulletSelection>>({});
  const [factOrder, setFactOrder] = useState<FactOrder>({});
  const [activeFactId, setActiveFactId] = useState<string | null>(null);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const [view, setView] = useState<View>("resume");
  const [showReport, setShowReport] = useState(false);
  const [livePreviewTex, setLivePreviewTex] = useState<string | null>(null);
  const [downloadBusy, setDownloadBusy] = useState<"pdf" | "tex" | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  useEffect(() => {
    getMaster()
      .then(setMaster)
      .catch(() => setMaster(null));
  }, []);

  const version = application?.version ?? null;

  useEffect(() => {
    if (!version) return;
    // Same stale-response guard as Tailor's JD preview -- a slower request
    // for an older set of selections must never overwrite a faster, newer one.
    let stale = false;
    const timer = setTimeout(async () => {
      try {
        const result = await previewApplication(id, selections, factOrder);
        if (!stale) setLivePreviewTex(result.tex);
      } catch {
        // keep showing the last good tex rather than blanking the pane
      }
    }, PREVIEW_DEBOUNCE_MS);
    return () => {
      stale = true;
      clearTimeout(timer);
    };
  }, [id, version, selections, factOrder]);

  const bulletsByFactId = useMemo(
    () => tailoredBulletsByFactId(version?.tailored ?? null),
    [version]
  );

  // Sourced from the version's own frozen snapshot, never the live master --
  // fact ids are assigned positionally at generation time (core/pipeline.py
  // _assign_ids) and are not stable across later master-resume edits. Reading
  // from a fresh getMaster() here could resolve a stale/reused fact id to the
  // wrong fact (or none), showing an AI rewrite as the user's own wording.
  const originalTextByFactId = useMemo(() => {
    const map = new Map<string, string>();
    if (!version?.source_facts) return map;
    for (const [factId, text] of Object.entries(version.source_facts)) map.set(factId, text);
    return map;
  }, [version]);

  const renderResume = useMemo(
    () =>
      master
        ? tailoredToRenderResume(master, version?.tailored ?? null, selections, factOrder)
        : null,
    [master, version, selections, factOrder]
  );

  // Where a fact currently sits within its own entry -- drives which
  // up/down arrow is enabled and what moveFact actually swaps.
  const factPositions = useMemo(() => {
    const map = new Map<string, { refId: string; index: number; length: number }>();
    if (!version?.tailored) return map;
    for (const section of [...version.tailored.experiences, ...version.tailored.projects]) {
      const order = factOrder[section.ref_id] ?? section.bullets.map((b) => b.source_fact_ids[0]);
      order.forEach((factId, index) => map.set(factId, { refId: section.ref_id, index, length: order.length }));
    }
    return map;
  }, [version, factOrder]);

  function moveFact(factId: string, direction: "up" | "down") {
    const position = factPositions.get(factId);
    if (!position) return;
    const swapWith = direction === "up" ? position.index - 1 : position.index + 1;
    if (swapWith < 0 || swapWith >= position.length) return;
    const current = [...factPositions.entries()]
      .filter(([, p]) => p.refId === position.refId)
      .sort((a, b) => a[1].index - b[1].index)
      .map(([id]) => id);
    [current[position.index], current[swapWith]] = [current[swapWith], current[position.index]];
    setFactOrder((prev) => ({ ...prev, [position.refId]: current }));
  }

  function updateSelection(factId: string, selection: BulletSelection) {
    setSelections((prev) => ({ ...prev, [factId]: selection }));
  }

  function changeView(next: View) {
    setView(next);
    setActiveFactId(null);
  }

  async function download(kind: "pdf" | "tex") {
    setDownloadBusy(kind);
    setDownloadError(null);
    // Open the tab synchronously, inside the click handler's transient-activation
    // window, so popup blockers see it as a direct response to the user's
    // gesture. We navigate it to the real URL once the (slow) finalize call
    // resolves, instead of calling window.open() after the await -- by then the
    // activation window has elapsed and Safari/Chrome silently block it.
    const tab = window.open("", "_blank");
    try {
      const updated = await finalizeApplication(id, selections, factOrder);
      const url = kind === "pdf" ? updated.pdf_url : updated.tex_url;
      const finalUrl = `${artifactUrl(url)}?v=${Date.now()}`;
      if (tab) {
        tab.location.href = finalUrl;
      } else {
        setDownloadError("Your browser blocked the download tab. Please allow pop-ups for this site and try again.");
      }
    } catch (e) {
      tab?.close();
      setDownloadError(e instanceof ApiError ? e.message : "Couldn't prepare that file.");
    } finally {
      setDownloadBusy(null);
    }
  }

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!application) return <p className="text-sm text-ink/60">Loading…</p>;

  if (application.status === "queued" || application.status === "running") {
    const runningLabel =
      application.mode === "tailor"
        ? "Rewriting your resume to match the posting…"
        : "Typesetting your resume…";
    return (
      <div className="flex flex-col items-center gap-2 py-16 text-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-em-softb border-t-em-accent" />
        <p className="text-sm text-ink/70">
          {application.status === "queued" ? "Queued…" : runningLabel}
        </p>
        {application.status === "running" && application.mode === "tailor" && (
          <p className="text-xs text-ink/50">
            Every line gets checked against your confirmed facts before it ships,
            so this can take up to a minute.
          </p>
        )}
      </div>
    );
  }

  if (application.status === "failed") {
    return (
      <div className="flex flex-col gap-3">
        <h1 className="font-serif text-xl font-semibold text-red-800">
          This one didn&apos;t go through.
        </h1>
        <pre className="overflow-auto whitespace-pre-wrap rounded-md bg-code-pane p-4 text-xs text-white/85">
          {application.error ?? "No error detail was recorded."}
        </pre>
      </div>
    );
  }

  if (!version) {
    return <p className="text-sm text-ink/60">Done, but no artifact was recorded.</p>;
  }

  const report = version.report;
  const tex = livePreviewTex ?? version.tex;

  return (
    // h-full, not a vh-minus-N guess: <main> in layout.tsx is now the sole
    // scroll container with a definite flex-1 height, so the toolbar row
    // below sizes to its own content and the flex-1 panel underneath just
    // gets whatever's actually left -- no pixel math to get wrong.
    <div className="flex h-full flex-col gap-4">
      {downloadError && <p className="shrink-0 text-sm text-red-700">{downloadError}</p>}

      <div className="shrink-0 flex flex-wrap items-center gap-4 rounded-lg border border-em-softb p-4">
        {report ? (
          <>
            <MatchScoreRing
              score={report.match_score}
              missingCount={report.missing_keywords.length}
            />
            <KeywordChips matched={report.matched_keywords} missing={report.missing_keywords} />
            <GroundedPill
              supportedCount={report.verdicts.filter((v) => v.supported).length}
              total={report.verdicts.length}
            />
            <button
              type="button"
              onClick={() => setShowReport((v) => !v)}
              className="text-xs font-medium text-em-deep underline hover:text-ink"
            >
              {showReport ? "Hide grounding report" : "Show grounding report"}
            </button>
          </>
        ) : (
          <span className="rounded-full bg-em-line-2 px-2.5 py-1 font-mono text-[11px] font-semibold text-em-muted-2">
            0 rewrites
          </span>
        )}

        <SegmentedControl
          value={view}
          onChange={changeView}
          options={[
            { value: "resume", label: "Resume" },
            { value: "tex", label: "LaTeX source" },
          ]}
        />
        <span className="text-xs text-ink/50">{VIEW_HINTS[view]}</span>

        <div className="ml-auto flex gap-2">
          <Button onClick={() => download("pdf")} disabled={downloadBusy !== null}>
            {downloadBusy === "pdf" ? "Preparing…" : "Download PDF"}
          </Button>
          <Button
            variant="secondary"
            onClick={() => download("tex")}
            disabled={downloadBusy !== null}
          >
            {downloadBusy === "tex" ? "Preparing…" : "Download .tex"}
          </Button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {view === "resume" ? (
          <div className="rounded-[10px] bg-em-line p-6.5">
            {renderResume && (
              <div className="mx-auto max-w-215 rounded-md bg-white px-16 py-13 shadow-lg">
                <ResumePaper
                  master={renderResume}
                  name={renderResume.name}
                  contact={[renderResume.email, renderResume.phone, ...renderResume.links]
                    .filter(Boolean)
                    .join(" | ")}
                  size="export"
                  hoveredKey={hoveredKey}
                  onHoverRow={setHoveredKey}
                  activeFactId={activeFactId}
                  onClickRow={(row) => {
                    const factId = row.factId;
                    if (!factId || !bulletsByFactId.has(factId)) return;
                    setActiveFactId((prev) => (prev === factId ? null : factId));
                  }}
                  renderRowControl={(row) => {
                    const bullet = row.factId ? bulletsByFactId.get(row.factId) : undefined;
                    if (!bullet || !row.factId) return null;
                    return (
                      <RewriteBar
                        key={row.factId}
                        bullet={bullet}
                        selection={selections[row.factId]}
                        originalText={
                          originalTextByFactId.get(row.factId) ??
                          "Original wording unavailable for this version."
                        }
                        onChangeSelection={(sel) => updateSelection(row.factId!, sel)}
                      />
                    );
                  }}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="h-full overflow-hidden rounded-lg border border-em-softb">
            <TexPane tex={tex} hoveredFactId={hoveredKey} onHoverFactId={setHoveredKey} />
          </div>
        )}

        {showReport && report && <ProvenancePanel verdicts={report.verdicts} />}
      </div>
    </div>
  );
}
