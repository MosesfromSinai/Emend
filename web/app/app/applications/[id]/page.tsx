"use client";

import { use, useEffect, useMemo, useState } from "react";

import { RewriteBar } from "@/components/export/rewrite-bar";
import { GroundedPill } from "@/components/grounded-pill";
import { KeywordChips } from "@/components/keyword-chips";
import { MatchScoreRing } from "@/components/match-score-ring";
import { ProvenancePanel } from "@/components/provenance-panel";
import { DEFAULT_SECTION_ORDER, ResumePaper, masterToSections } from "@/components/resume-paper";
import { TexPane } from "@/components/tex-pane";
import { Button } from "@/components/ui/button";
import { SegmentedControl } from "@/components/ui/segmented-control";
import {
  ApiError,
  artifactUrl,
  finalizeApplication,
  getMaster,
  previewApplication,
  type RenderOptions,
} from "@/lib/api";
import { excludeByKey, reorderByKey } from "@/lib/order";
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
  const [experienceOrder, setExperienceOrder] = useState<string[]>([]);
  const [projectOrder, setProjectOrder] = useState<string[]>([]);
  const [sectionOrder, setSectionOrder] = useState<string[]>([]);
  const [excludedFacts, setExcludedFacts] = useState<string[]>([]);
  const [excludedExperiences, setExcludedExperiences] = useState<string[]>([]);
  const [excludedProjects, setExcludedProjects] = useState<string[]>([]);
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

  // Single bag of "what the user has changed on Export" -- fed to both the
  // live preview effect below and finalize() on download, so the two never
  // drift out of sync with each other.
  const renderOptions: RenderOptions = {
    selections,
    factOrder,
    experienceOrder,
    projectOrder,
    sectionOrder,
    excludedFacts,
    excludedExperiences,
    excludedProjects,
  };

  useEffect(() => {
    if (!version) return;
    // Same stale-response guard as Tailor's JD preview -- a slower request
    // for an older set of selections must never overwrite a faster, newer one.
    let stale = false;
    const timer = setTimeout(async () => {
      try {
        const result = await previewApplication(id, renderOptions);
        if (!stale) setLivePreviewTex(result.tex);
      } catch {
        // keep showing the last good tex rather than blanking the pane
      }
    }, PREVIEW_DEBOUNCE_MS);
    return () => {
      stale = true;
      clearTimeout(timer);
    };
  }, [
    id,
    version,
    selections,
    factOrder,
    experienceOrder,
    projectOrder,
    sectionOrder,
    excludedFacts,
    excludedExperiences,
    excludedProjects,
  ]);

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
        ? tailoredToRenderResume(
            master,
            version?.tailored ?? null,
            selections,
            factOrder,
            experienceOrder,
            projectOrder,
            excludedFacts,
            excludedExperiences,
            excludedProjects
          )
        : null,
    [
      master,
      version,
      selections,
      factOrder,
      experienceOrder,
      projectOrder,
      excludedFacts,
      excludedExperiences,
      excludedProjects,
    ]
  );

  // The currently-visible section headings (empty sections don't render),
  // reordered by the user's saved preference -- reordering against what's
  // actually on screen, not the full 4-key space, keeps adjacent-arrow
  // enablement correct even as sections appear/disappear with edits.
  const effectiveSectionOrder = useMemo(() => {
    const visibleKeys = renderResume
      ? masterToSections(renderResume).map((s) => s.key)
      : DEFAULT_SECTION_ORDER;
    return reorderByKey(visibleKeys, sectionOrder, (k) => k);
  }, [renderResume, sectionOrder]);

  function moveSection(key: string, direction: "up" | "down") {
    const idx = effectiveSectionOrder.indexOf(key);
    if (idx === -1) return;
    const swapWith = direction === "up" ? idx - 1 : idx + 1;
    if (swapWith < 0 || swapWith >= effectiveSectionOrder.length) return;
    const next = [...effectiveSectionOrder];
    [next[idx], next[swapWith]] = [next[swapWith], next[idx]];
    setSectionOrder(next);
  }

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

  // Where an experience/project entry currently sits among its own kind --
  // drives which up/down arrow is enabled on that entry's header.
  const entryPositions = useMemo(() => {
    const map = new Map<string, { kind: "experience" | "project"; index: number; length: number }>();
    if (!version?.tailored) return map;
    const expOrder = experienceOrder.length
      ? experienceOrder
      : version.tailored.experiences.map((s) => s.ref_id);
    expOrder.forEach((refId, index) => map.set(refId, { kind: "experience", index, length: expOrder.length }));
    const projOrder = projectOrder.length
      ? projectOrder
      : version.tailored.projects.map((s) => s.ref_id);
    projOrder.forEach((refId, index) => map.set(refId, { kind: "project", index, length: projOrder.length }));
    return map;
  }, [version, experienceOrder, projectOrder]);

  function moveEntry(refId: string, direction: "up" | "down") {
    const position = entryPositions.get(refId);
    if (!position) return;
    const swapWith = direction === "up" ? position.index - 1 : position.index + 1;
    if (swapWith < 0 || swapWith >= position.length) return;
    const current = [...entryPositions.entries()]
      .filter(([, p]) => p.kind === position.kind)
      .sort((a, b) => a[1].index - b[1].index)
      .map(([id]) => id);
    [current[position.index], current[swapWith]] = [current[swapWith], current[position.index]];
    if (position.kind === "experience") setExperienceOrder(current);
    else setProjectOrder(current);
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
      const updated = await finalizeApplication(id, renderOptions);
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
                    const position = factPositions.get(row.factId);
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
                        canMoveUp={position ? position.index > 0 : false}
                        canMoveDown={position ? position.index < position.length - 1 : false}
                        onMove={(direction) => moveFact(row.factId!, direction)}
                      />
                    );
                  }}
                  renderBlockControl={(block) => {
                    const position = entryPositions.get(block.key);
                    if (!position) return null;
                    return (
                      <div className="flex gap-1">
                        <button
                          type="button"
                          onClick={() => moveEntry(block.key, "up")}
                          disabled={position.index === 0}
                          aria-label={`Move ${block.title} up`}
                          className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-ink hover:border-ink disabled:cursor-default disabled:opacity-30 disabled:hover:border-em-softb"
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          onClick={() => moveEntry(block.key, "down")}
                          disabled={position.index === position.length - 1}
                          aria-label={`Move ${block.title} down`}
                          className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-ink hover:border-ink disabled:cursor-default disabled:opacity-30 disabled:hover:border-em-softb"
                        >
                          ↓
                        </button>
                      </div>
                    );
                  }}
                  sectionOrder={effectiveSectionOrder}
                  renderSectionControl={(section) => {
                    const idx = effectiveSectionOrder.indexOf(section.key);
                    return (
                      <div className="flex gap-1">
                        <button
                          type="button"
                          onClick={() => moveSection(section.key, "up")}
                          disabled={idx <= 0}
                          aria-label={`Move ${section.heading} section up`}
                          className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-ink hover:border-ink disabled:cursor-default disabled:opacity-30 disabled:hover:border-em-softb"
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          onClick={() => moveSection(section.key, "down")}
                          disabled={idx === -1 || idx >= effectiveSectionOrder.length - 1}
                          aria-label={`Move ${section.heading} section down`}
                          className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-ink hover:border-ink disabled:cursor-default disabled:opacity-30 disabled:hover:border-em-softb"
                        >
                          ↓
                        </button>
                      </div>
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
