"use client";

import Link from "next/link";
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
import { DeleteButton } from "@/components/ui/delete-button";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { TailoringProgress } from "@/components/tailoring-progress";
import {
  ApiError,
  artifactUrl,
  finalizeApplication,
  getMaster,
  polishApplication,
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
  resume: "Click any line to edit it.",
  tex: "Every generated line carries a % grounded receipt.",
};

// mirrors latex/render.py's default_headings
const DEFAULT_SECTION_HEADINGS: Record<string, string> = {
  EDUCATION: "Education",
  EXPERIENCE: "Experience",
  PROJECTS: "Projects",
  SKILLS: "Technical Skills",
};

// Every edit on this page previously lived only in React state -- navigate
// away (even just back to Confirm and back) and it was gone. sessionStorage
// (cleared when the tab closes, same mechanism as the fresh-visit gate on
// /app) keyed per application id fixes that without resurrecting stale
// edits from a completely different session days later.
type SavedEdits = Partial<{
  selections: Record<string, BulletSelection>;
  factOrder: FactOrder;
  experienceOrder: string[];
  projectOrder: string[];
  sectionOrder: string[];
  textOverrides: Record<string, string>;
  excludedFacts: string[];
  excludedExperiences: string[];
  excludedProjects: string[];
}>;

function savedEditsKey(id: string): string {
  return `emend_export_edits_${id}`;
}

function loadSavedEdits(id: string): SavedEdits {
  try {
    const raw = sessionStorage.getItem(savedEditsKey(id));
    return raw ? (JSON.parse(raw) as SavedEdits) : {};
  } catch {
    return {};
  }
}

export default function ApplicationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { application, error, restartPolling } = usePollApplication(id);
  const [polishBusy, setPolishBusy] = useState(false);
  const [polishError, setPolishError] = useState<string | null>(null);
  const [master, setMaster] = useState<MasterResume | null>(null);
  const [selections, setSelections] = useState<Record<string, BulletSelection>>(
    () => loadSavedEdits(id).selections ?? {}
  );
  const [factOrder, setFactOrder] = useState<FactOrder>(() => loadSavedEdits(id).factOrder ?? {});
  const [experienceOrder, setExperienceOrder] = useState<string[]>(
    () => loadSavedEdits(id).experienceOrder ?? []
  );
  const [projectOrder, setProjectOrder] = useState<string[]>(
    () => loadSavedEdits(id).projectOrder ?? []
  );
  const [sectionOrder, setSectionOrder] = useState<string[]>(
    () => loadSavedEdits(id).sectionOrder ?? []
  );
  const [textOverrides, setTextOverrides] = useState<Record<string, string>>(
    () => loadSavedEdits(id).textOverrides ?? {}
  );
  const [excludedFacts, setExcludedFacts] = useState<string[]>(
    () => loadSavedEdits(id).excludedFacts ?? []
  );
  const [excludedExperiences, setExcludedExperiences] = useState<string[]>(
    () => loadSavedEdits(id).excludedExperiences ?? []
  );
  const [excludedProjects, setExcludedProjects] = useState<string[]>(
    () => loadSavedEdits(id).excludedProjects ?? []
  );
  const [activeFactId, setActiveFactId] = useState<string | null>(null);
  const [activeRowKey, setActiveRowKey] = useState<string | null>(null);
  const [activeBlockField, setActiveBlockField] = useState<{
    blockKey: string;
    field: "title" | "sub" | "dates";
  } | null>(null);
  const [activeHeaderField, setActiveHeaderField] = useState<"name" | "contact" | null>(null);
  const [activeSectionHeadingKey, setActiveSectionHeadingKey] = useState<string | null>(null);
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

  // Education has no stable id in the schema (unlike experience/project,
  // which key overrides off the entry's own id) -- `education:<i>:*`
  // overrides are keyed by array position instead. Combined with these
  // overrides now surviving in sessionStorage across visits, editing the
  // master resume's education list (removing an entry) between saves could
  // otherwise leave a stale override silently pointed at whatever now sits
  // at that index. This prunes overrides whose index no longer exists;
  // it can't detect a *reordered* (but still in-range) entry, which would
  // need a real per-entry id -- a schema/contract change, not a quick fix.
  useEffect(() => {
    if (!master) return;
    // Synchronizing against master (an external, asynchronously-loaded
    // resource) loading/changing -- not state derivable during render, and
    // the functional updater bails out to the same `prev` reference (a
    // React no-op) when nothing is actually stale.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTextOverrides((prev) => {
      const validCount = master.education.length;
      const next: Record<string, string> = {};
      let changed = false;
      for (const [key, value] of Object.entries(prev)) {
        const match = key.match(/^education:(\d+):/);
        if (match && Number(match[1]) >= validCount) {
          changed = true;
          continue;
        }
        next[key] = value;
      }
      return changed ? next : prev;
    });
  }, [master]);

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
    const edits: SavedEdits = renderOptions;
    try {
      sessionStorage.setItem(savedEditsKey(id), JSON.stringify(edits));
    } catch {
      // Safari private browsing throws on setItem; storage quota can too on
      // a very large pasted override. Either way, losing edit persistence
      // for this tab is a much smaller problem than an uncaught throw here
      // breaking every future edit on the page.
    }
    // renderOptions is a fresh object every render (see the debounce effect
    // below for why) -- depend on its actual fields instead.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    id,
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
    const [kind, a, b, c] = key.split(":");
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
    if (kind === "custom") {
      const entry = renderResume.custom_sections
        .flatMap((cs) => cs.entries)
        .find((e) => e.id === a);
      if (!entry) return "";
      if (b === "title") return entry.title;
      if (b === "subtitle") return entry.subtitle;
      if (b === "location") return entry.location;
      if (b === "start") return entry.start;
      if (b === "end") return entry.end;
      if (b === "fact") return entry.facts.find((f) => f.id === c)?.text ?? "";
    }
    if (kind === "section" && b === "heading") {
      return textOverrides[key] ?? defaultHeadingFor(a) ?? "";
    }
    return "";
  }

  // The fixed four sections have a hardcoded default; a custom section's
  // "default" is just its own confirmed heading, since it has no built-in
  // one -- the user named it themselves back on Confirm.
  function defaultHeadingFor(key: string): string {
    if (DEFAULT_SECTION_HEADINGS[key]) return DEFAULT_SECTION_HEADINGS[key];
    return renderResume?.custom_sections.find((cs) => cs.key === key)?.heading ?? "";
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
    setActiveSectionHeadingKey(null);
  }

  function changeView(next: View) {
    setView(next);
    // Not just setActiveFactId(null): a keyboard-driven view switch (Tab to
    // the segmented control, Enter/Space) dispatches a synthetic click with
    // no preceding mousedown, so the outside-click handler below never
    // fires to close a different kind of open editor (a header/block/
    // section field) -- clear all five here too, or it silently reopens,
    // unclicked, when the Resume view remounts.
    clearActiveEditors();
  }

  // Clicking off the resume paper closes whatever line is being edited --
  // clicks inside it are already handled by each row/field's own onClick
  // (contains() is true for those, so this is a no-op there).
  useEffect(() => {
    function handleOutsideClick(e: MouseEvent) {
      if (paperRef.current && !paperRef.current.contains(e.target as Node)) {
        clearActiveEditors();
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const hasAnyEdits =
    Object.keys(selections).length > 0 ||
    Object.keys(factOrder).length > 0 ||
    experienceOrder.length > 0 ||
    projectOrder.length > 0 ||
    sectionOrder.length > 0 ||
    Object.keys(textOverrides).length > 0 ||
    excludedFacts.length > 0 ||
    excludedExperiences.length > 0 ||
    excludedProjects.length > 0;

  function resetAllEdits() {
    if (!window.confirm("Discard every edit made on this export? This can't be undone.")) return;
    setSelections({});
    setFactOrder({});
    setExperienceOrder([]);
    setProjectOrder([]);
    setSectionOrder([]);
    setTextOverrides({});
    setExcludedFacts([]);
    setExcludedExperiences([]);
    setExcludedProjects([]);
    clearActiveEditors();
    sessionStorage.removeItem(savedEditsKey(id));
  }

  // "Sam Reyes" -> "Sam_Reyes_Resume.pdf"; a middle name/initial is dropped
  // ("Moses A. Vila" -> "Moses_Vila_Resume.pdf") rather than included, so
  // the filename stays first-and-last regardless of how many words are in
  // between. Falls back to a plain "Resume.ext" if the name is missing or
  // has nothing filename-safe in it.
  function resumeFileName(name: string, extension: "pdf" | "tex"): string {
    const parts = name
      .trim()
      .split(/\s+/)
      // NFKD splits an accented letter into its base letter + a separate
      // combining mark ("é" -> "e" + ́), so stripping the marks first
      // turns "José" into a readable "Jose" instead of a mangled "Jos" --
      // a name in a script with no Latin decomposition at all (Chinese,
      // Arabic...) still strips to nothing and correctly falls through to
      // the plain "Resume.ext" fallback below, same as an empty name.
      .map((part) =>
        part
          .normalize("NFKD")
          .replace(/[\u0300-\u036f]/g, "")
          .replace(/[^a-zA-Z0-9'-]/g, "")
      )
      .filter(Boolean);
    const firstLast = parts.length > 1 ? [parts[0], parts[parts.length - 1]] : parts;
    const base = firstLast.length > 0 ? `${firstLast.join("_")}_Resume` : "Resume";
    return `${base}.${extension}`;
  }

  async function download(kind: "pdf" | "tex") {
    setDownloadBusy(kind);
    setDownloadError(null);
    // Fetching the file ourselves and saving it via a blob URL, instead of
    // navigating a tab to the artifact URL, means no new tab and no leaving
    // this page at all -- and it's the only way to get a real filename on
    // it, since <a download> is ignored by browsers for a cross-origin href
    // (the API and the web app are on different domains in production).
    try {
      const updated = await finalizeApplication(id, renderOptions);
      const url = kind === "pdf" ? updated.pdf_url : updated.tex_url;
      const response = await fetch(`${artifactUrl(url)}?v=${Date.now()}`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("download failed");
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const name = renderResume?.name ?? master?.name ?? "";
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = resumeFileName(name, kind);
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (e) {
      setDownloadError(e instanceof ApiError ? e.message : "Couldn't prepare that file.");
    } finally {
      setDownloadBusy(null);
    }
  }

  async function startPolish() {
    if (
      !window.confirm(
        "This uses AI to rewrite your bullets for stronger, more professional wording. " +
          "Every line still gets checked against your confirmed facts, so nothing gets " +
          "invented -- just phrased better. Continue?"
      )
    ) {
      return;
    }
    setPolishBusy(true);
    setPolishError(null);
    try {
      await polishApplication(id);
      restartPolling();
    } catch (e) {
      setPolishError(e instanceof ApiError ? e.message : "Couldn't start that.");
      setPolishBusy(false);
    }
  }

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!application) return <p className="text-sm text-ink/60">Loading…</p>;

  if (application.status === "queued" || application.status === "running") {
    const runningLabel =
      application.mode === "tailor"
        ? "Rewriting your resume to match the posting…"
        : application.mode === "polish"
          ? "Rewriting your resume to sound as strong as possible…"
          : "Typesetting your resume…";
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <p className="text-sm text-ink/70">
          {application.status === "queued" ? "Queued…" : runningLabel}
        </p>
        <TailoringProgress mode={application.mode} />
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
        <Link
          href="/app/workspace"
          className="w-fit text-sm font-medium text-em-accent hover:text-em-deep"
        >
          ← Back to Tailor, try again
        </Link>
      </div>
    );
  }

  if (!version) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-sm text-ink/60">Done, but no artifact was recorded.</p>
        <Link
          href="/app/workspace"
          className="w-fit text-sm font-medium text-em-accent hover:text-em-deep"
        >
          ← Back to Tailor, try again
        </Link>
      </div>
    );
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
          <>
            <span className="rounded-full bg-em-line-2 px-2.5 py-1 font-mono text-[11px] font-semibold text-em-muted-2">
              0 rewrites
            </span>
            <button
              type="button"
              onClick={startPolish}
              disabled={polishBusy}
              className="text-xs font-medium text-em-accent hover:text-em-deep disabled:opacity-60"
            >
              {polishBusy
                ? "Starting…"
                : "Want to make this as strong as possible, professionally? Click here."}
            </button>
          </>
        )}
        {polishError && <p className="text-xs text-red-700">{polishError}</p>}

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
          {hasAnyEdits && (
            <button
              type="button"
              onClick={resetAllEdits}
              className="text-xs text-red-700 underline hover:text-red-900"
            >
              Reset all edits
            </button>
          )}
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
            <p className="mx-auto mb-3 max-w-215 text-center text-xs text-ink/50">
              Click any line to edit it — your name, contact info, headings, dates, and bullets.
              Click elsewhere to close it.
            </p>
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
              <div ref={paperRef} className="mx-auto max-w-215 rounded-md bg-white px-16 py-13 shadow-lg">
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
                    const wasActive = row.factId === activeFactId || row.key === activeRowKey;
                    clearActiveEditors();
                    if (wasActive) return;
                    const factId = row.factId;
                    if (factId && bulletsByFactId.has(factId)) {
                      setActiveFactId(factId);
                      return;
                    }
                    if (row.overrideKey) setActiveRowKey(row.key);
                  }}
                  renderRowControl={(row) => {
                    if (row.overrideKey && row.key === activeRowKey) {
                      return (
                        <OverrideEditor
                          key={row.key}
                          fields={[
                            {
                              key: row.overrideKey,
                              label: labelForKey(row.overrideKey),
                              value: currentOverrideValue(row.overrideKey),
                              onDelete: () => clearOverrides([row.overrideKey!]),
                            },
                          ]}
                          onChange={updateTextOverride}
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
                    if (!position) return null;
                    return (
                      <div className="flex items-center gap-1">
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
                        <DeleteButton
                          onClick={() => deleteEntry(block.key, position.kind)}
                          label={`Delete ${block.title}`}
                        />
                      </div>
                    );
                  }}
                  activeBlockField={activeBlockField}
                  onClickBlockField={(block, field) => {
                    const wasActive =
                      activeBlockField?.blockKey === block.key && activeBlockField.field === field;
                    clearActiveEditors();
                    if (!wasActive) setActiveBlockField({ blockKey: block.key, field });
                  }}
                  renderBlockFieldControl={(block, field) => {
                    const keys =
                      field === "title"
                        ? block.titleOverrideKeys
                        : field === "sub"
                          ? block.subOverrideKeys
                          : block.datesOverrideKeys;
                    if (keys.length === 0) return null;
                    return (
                      <OverrideEditor
                        fields={keys.map((key) => ({
                          key,
                          label: labelForKey(key),
                          value: currentOverrideValue(key),
                          onDelete: () => clearOverrides([key]),
                        }))}
                        onChange={updateTextOverride}
                      />
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
                  sectionHeadings={Object.fromEntries(
                    effectiveSectionOrder.map((key) => [key, currentOverrideValue(`section:${key}:heading`)])
                  )}
                  activeSectionHeadingKey={activeSectionHeadingKey}
                  onClickSectionHeading={(section) => {
                    const wasActive = activeSectionHeadingKey === section.key;
                    clearActiveEditors();
                    if (!wasActive) setActiveSectionHeadingKey(section.key);
                  }}
                  renderSectionHeadingControl={(section) => (
                    <OverrideEditor
                      fields={[
                        {
                          key: section.headingOverrideKey,
                          label: "Heading",
                          value: currentOverrideValue(section.headingOverrideKey),
                          onDelete: () => {
                            // "delete" resets the rename rather than
                            // blanking it -- an empty \section{} divider
                            // helps no one
                            updateTextOverride(
                              section.headingOverrideKey,
                              defaultHeadingFor(section.key)
                            );
                            clearActiveEditors();
                          },
                        },
                      ]}
                      onChange={updateTextOverride}
                    />
                  )}
                  activeHeaderField={activeHeaderField}
                  onClickHeaderField={(field) => {
                    const wasActive = activeHeaderField === field;
                    clearActiveEditors();
                    if (!wasActive) setActiveHeaderField(field);
                  }}
                  renderHeaderFieldControl={(field) => {
                    if (field === "name") {
                      return (
                        <OverrideEditor
                          fields={[
                            {
                              key: "name",
                              label: "Name",
                              value: currentOverrideValue("name"),
                              onDelete: () => clearOverrides(["name"]),
                            },
                          ]}
                          onChange={updateTextOverride}
                        />
                      );
                    }
                    const keys = ["email", "phone", ...renderResume.links.map((_, i) => `link:${i}`)];
                    return (
                      <OverrideEditor
                        fields={keys.map((key) => ({
                          key,
                          label: labelForKey(key),
                          value: currentOverrideValue(key),
                          onDelete: () => clearOverrides([key]),
                        }))}
                        onChange={updateTextOverride}
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
