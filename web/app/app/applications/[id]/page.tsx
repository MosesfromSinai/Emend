"use client";

import { use, useEffect, useMemo, useRef, useState } from "react";

import { OverrideEditor } from "@/components/export/override-editor";
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
  const [textOverrides, setTextOverrides] = useState<Record<string, string>>({});
  const [excludedFacts, setExcludedFacts] = useState<string[]>([]);
  const [excludedExperiences, setExcludedExperiences] = useState<string[]>([]);
  const [excludedProjects, setExcludedProjects] = useState<string[]>([]);
  const [activeFactId, setActiveFactId] = useState<string | null>(null);
  const [activeRowKey, setActiveRowKey] = useState<string | null>(null);
  const [activeBlockField, setActiveBlockField] = useState<{
    blockKey: string;
    field: "title" | "sub" | "dates";
  } | null>(null);
  const [activeHeaderField, setActiveHeaderField] = useState<"name" | "contact" | null>(null);
  const paperRef = useRef<HTMLDivElement>(null);
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
    textOverrides,
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
    // renderOptions is a fresh object every render -- depending on it
    // directly would re-fire this debounced effect on every render instead
    // of only when one of its underlying fields actually changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    textOverrides,
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
            excludedProjects,
            textOverrides
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
      textOverrides,
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
      const liveIds = excludeByKey(
        section.bullets.map((b) => b.source_fact_ids[0]),
        excludedFacts,
        (id) => id
      );
      const order = reorderByKey(liveIds, factOrder[section.ref_id], (id) => id);
      order.forEach((factId, index) => map.set(factId, { refId: section.ref_id, index, length: order.length }));
    }
    return map;
  }, [version, factOrder, excludedFacts]);

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
    const liveExpIds = excludeByKey(
      version.tailored.experiences.map((s) => s.ref_id),
      excludedExperiences,
      (id) => id
    );
    const expOrder = reorderByKey(liveExpIds, experienceOrder, (id) => id);
    expOrder.forEach((refId, index) => map.set(refId, { kind: "experience", index, length: expOrder.length }));
    const liveProjIds = excludeByKey(
      version.tailored.projects.map((s) => s.ref_id),
      excludedProjects,
      (id) => id
    );
    const projOrder = reorderByKey(liveProjIds, projectOrder, (id) => id);
    projOrder.forEach((refId, index) => map.set(refId, { kind: "project", index, length: projOrder.length }));
    return map;
  }, [version, experienceOrder, projectOrder, excludedExperiences, excludedProjects]);

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

  // Deleting is export-time only: it hides a bullet/entry from this
  // rendered output, never the confirmed master resume or the stored
  // tailored version -- so "undo" is just removing the id again, no
  // separate confirm step needed.
  function deleteFact(factId: string) {
    setExcludedFacts((prev) => (prev.includes(factId) ? prev : [...prev, factId]));
    setActiveFactId(null);
  }

  function restoreFact(factId: string) {
    setExcludedFacts((prev) => prev.filter((id) => id !== factId));
  }

  function deleteEntry(refId: string, kind: "experience" | "project") {
    if (kind === "experience") {
      setExcludedExperiences((prev) => (prev.includes(refId) ? prev : [...prev, refId]));
    } else {
      setExcludedProjects((prev) => (prev.includes(refId) ? prev : [...prev, refId]));
    }
  }

  function restoreEntry(refId: string, kind: "experience" | "project") {
    if (kind === "experience") setExcludedExperiences((prev) => prev.filter((id) => id !== refId));
    else setExcludedProjects((prev) => prev.filter((id) => id !== refId));
  }

  // Everything currently hidden from this export, so deleting never feels
  // like a one-way door -- each entry restores with a single click.
  const removedItems = useMemo(() => {
    const items: { key: string; label: string; restore: () => void }[] = [];
    if (!version?.tailored) return items;
    for (const section of [...version.tailored.experiences, ...version.tailored.projects]) {
      for (const bullet of section.bullets) {
        const factId = bullet.source_fact_ids[0];
        if (!excludedFacts.includes(factId)) continue;
        const text = bullet.variants[0];
        items.push({
          key: `fact-${factId}`,
          label: text.length > 50 ? `${text.slice(0, 50)}…` : text,
          restore: () => restoreFact(factId),
        });
      }
    }
    for (const section of version.tailored.experiences) {
      if (!excludedExperiences.includes(section.ref_id)) continue;
      const exp = master?.experiences.find((e) => e.id === section.ref_id);
      items.push({
        key: `exp-${section.ref_id}`,
        label: exp?.company ?? section.ref_id,
        restore: () => restoreEntry(section.ref_id, "experience"),
      });
    }
    for (const section of version.tailored.projects) {
      if (!excludedProjects.includes(section.ref_id)) continue;
      const proj = master?.projects.find((p) => p.id === section.ref_id);
      items.push({
        key: `proj-${section.ref_id}`,
        label: proj?.name ?? section.ref_id,
        restore: () => restoreEntry(section.ref_id, "project"),
      });
    }
    return items;
  }, [version, master, excludedFacts, excludedExperiences, excludedProjects]);

  function updateSelection(factId: string, selection: BulletSelection) {
    setSelections((prev) => ({ ...prev, [factId]: selection }));
  }

  // Free-text edits to anything that isn't a fact-backed bullet -- header
  // info, education, skills, structural entry fields. Separate from
  // selections/updateSelection above, which stays scoped to confirmed facts.
  function updateTextOverride(key: string, value: string) {
    setTextOverrides((prev) => ({ ...prev, [key]: value }));
  }

  // The current effective (already-overridden) raw value for a given
  // text_overrides path -- used to seed an editor's starting text, since
  // a row's display text (e.g. "Coursework: A, B.") isn't the raw value.
  function currentOverrideValue(key: string): string {
    if (!renderResume) return "";
    const [kind, a, b] = key.split(":");
    if (kind === "name") return renderResume.name;
    if (kind === "email") return renderResume.email;
    if (kind === "phone") return renderResume.phone;
    if (kind === "link") return renderResume.links[Number(a)] ?? "";
    if (kind === "education") {
      const edu = renderResume.education[Number(a)];
      if (!edu) return "";
      if (b === "coursework") return edu.coursework.join(", ");
      if (b === "school") return edu.school;
      if (b === "degree") return edu.degree;
      if (b === "location") return edu.location;
      if (b === "grad_date") return edu.grad_date;
    }
    if (kind === "experience") {
      const exp = renderResume.experiences.find((e) => e.id === a);
      if (!exp) return "";
      if (b === "title") return exp.title;
      if (b === "company") return exp.company;
      if (b === "location") return exp.location;
      if (b === "start") return exp.start;
      if (b === "end") return exp.end;
    }
    if (kind === "project") {
      const proj = renderResume.projects.find((p) => p.id === a);
      if (!proj) return "";
      if (b === "name") return proj.name;
      if (b === "tech") return proj.tech.join(", ");
    }
    if (kind === "skills") {
      const category = key.slice("skills:".length);
      return (renderResume.skills[category] ?? []).join(", ");
    }
    return "";
  }

  // A short human label derived from a text_overrides path's own key
  // segments -- "experience:ACME:start" -> "Start" -- so OverrideEditor
  // never needs a lookup table to know what it's showing.
  function labelForKey(key: string): string {
    if (key.startsWith("link:")) return `Link ${Number(key.split(":")[1]) + 1}`;
    const last = key.split(":").pop() ?? key;
    const spaced = last.replace(/_/g, " ");
    return spaced.charAt(0).toUpperCase() + spaced.slice(1);
  }

  // Deleting a line clears every key it represents (a composite line like
  // "company — location" is two keys) and closes whatever editor was open.
  function clearOverrides(keys: string[]) {
    setTextOverrides((prev) => {
      const next = { ...prev };
      for (const key of keys) next[key] = "";
      return next;
    });
    clearActiveEditors();
  }

  // Only one editor -- a bullet, a coursework/skills line, a structural
  // field, or a header field -- is ever open at once.
  function clearActiveEditors() {
    setActiveFactId(null);
    setActiveRowKey(null);
    setActiveBlockField(null);
    setActiveHeaderField(null);
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
            {removedItems.length > 0 && (
              <div className="mx-auto mb-4 flex max-w-215 flex-wrap items-center gap-2 rounded-lg border border-em-softb bg-white px-3 py-2 text-xs text-ink/70">
                <span className="font-semibold text-ink">
                  {removedItems.length} removed from this export:
                </span>
                {removedItems.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    onClick={item.restore}
                    className="rounded-full border border-em-softb px-2 py-0.5 hover:border-ink hover:text-ink"
                  >
                    {item.label} · restore
                  </button>
                ))}
              </div>
            )}
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
                  activeRowKey={activeRowKey}
                  onClickRow={(row) => {
                    const factId = row.factId;
                    if (factId && bulletsByFactId.has(factId)) {
                      setActiveFactId((prev) => (prev === factId ? null : factId));
                      setActiveRowKey(null);
                      return;
                    }
                    if (row.overrideKey) {
                      setActiveRowKey((prev) => (prev === row.key ? null : row.key));
                      setActiveFactId(null);
                    }
                  }}
                  renderRowControl={(row) => {
                    if (row.overrideKey && row.key === activeRowKey) {
                      return (
                        <OverrideEditor
                          key={row.key}
                          label="edit this line"
                          value={currentOverrideValue(row.overrideKey)}
                          onChange={(text) => updateTextOverride(row.overrideKey!, text)}
                        />
                      );
                    }
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
                        onDelete={() => deleteFact(row.factId!)}
                      />
                    );
                  }}
                  renderBlockControl={(block) => {
                    const position = entryPositions.get(block.key);
                    const isEducation = block.key.startsWith("edu-");
                    if (!position && !isEducation) return null;
                    return (
                      <div className="flex gap-1">
                        {position && (
                          <>
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
                            <button
                              type="button"
                              onClick={() => deleteEntry(block.key, position.kind)}
                              aria-label={`Delete ${block.title}`}
                              className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-red-700 hover:border-red-700"
                            >
                              delete
                            </button>
                          </>
                        )}
                        <button
                          type="button"
                          onClick={() => setActiveEntryEdit((prev) => (prev === block.key ? null : block.key))}
                          aria-label={`Edit ${block.title} details`}
                          className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-em-deep underline hover:border-ink"
                        >
                          {activeEntryEdit === block.key ? "done" : "edit details"}
                        </button>
                      </div>
                    );
                  }}
                  renderBlockExtra={(block) => {
                    if (activeEntryEdit !== block.key) return null;
                    const isEducation = block.key.startsWith("edu-");
                    const fields = isEducation
                      ? [
                          overrideField("School", `education:${block.key.slice(4)}:school`),
                          overrideField("Degree", `education:${block.key.slice(4)}:degree`),
                          overrideField("Location", `education:${block.key.slice(4)}:location`),
                          overrideField("Graduation date", `education:${block.key.slice(4)}:grad_date`),
                          overrideField("Coursework", `education:${block.key.slice(4)}:coursework`),
                        ]
                      : entryPositions.get(block.key)?.kind === "project"
                        ? [
                            overrideField("Project name", `project:${block.key}:name`),
                            overrideField("Tech", `project:${block.key}:tech`),
                          ]
                        : [
                            overrideField("Title", `experience:${block.key}:title`),
                            overrideField("Company", `experience:${block.key}:company`),
                            overrideField("Location", `experience:${block.key}:location`),
                            overrideField("Start date", `experience:${block.key}:start`),
                            overrideField("End date", `experience:${block.key}:end`),
                          ];
                    return (
                      <div className="mb-2 rounded-lg border border-em-softb bg-em-soft p-3 text-xs">
                        <div className="flex flex-col gap-2">{fields}</div>
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
                  renderHeaderControl={() => (
                    <button
                      type="button"
                      onClick={() => setHeaderEditOpen((v) => !v)}
                      className="ml-2 align-middle text-xs font-normal text-em-deep underline hover:text-ink"
                    >
                      {headerEditOpen ? "done editing" : "edit"}
                    </button>
                  )}
                  renderHeaderExtra={() =>
                    headerEditOpen ? (
                      <div className="mx-auto mb-4 max-w-sm rounded-lg border border-em-softb bg-em-soft p-3 text-left text-xs">
                        <div className="mb-2 font-semibold text-ink">Edit header</div>
                        <div className="flex flex-col gap-2">
                          {overrideField("Name", "name")}
                          {overrideField("Email", "email")}
                          {overrideField("Phone", "phone")}
                          {renderResume?.links.map((_, i) => overrideField(`Link ${i + 1}`, `link:${i}`))}
                        </div>
                      </div>
                    ) : null
                  }
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
