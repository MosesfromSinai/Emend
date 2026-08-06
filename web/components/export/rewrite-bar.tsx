"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";
import type { BulletSelection, TailoredBullet } from "@/lib/types";

// Rendered inline, directly beneath the active bullet on the resume paper
// (via ResumePaper's renderRowControl slot) -- never a page-level bar.
// Parent must pass `key={factId}` so state resets when the active bullet
// changes, same reasoning as before this was made inline.
export function RewriteBar({
  bullet,
  selection,
  originalText,
  onChangeSelection,
  canMoveUp,
  canMoveDown,
  onMove,
  onDelete,
}: {
  bullet: TailoredBullet;
  selection?: BulletSelection;
  originalText: string;
  onChangeSelection: (selection: BulletSelection) => void;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
  onMove?: (direction: "up" | "down") => void;
  onDelete?: () => void;
}) {
  const [viewingOriginal, setViewingOriginal] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  const variantIdx = selection?.variantIdx ?? 0;
  const isCustom = Boolean(selection?.customText);
  const currentText = selection?.customText ?? bullet.variants[variantIdx];
  const showDiscard = isCustom || (editing && draft !== currentText);
  // Refactor mode (no job posting) wraps each fact as 3 identical variants
  // just so this same edit UI works there too -- cycling through three
  // copies of the same sentence would be confusing, so hide that control
  // and say so plainly instead of "rewrite 1 of 3."
  const hasRealVariants = bullet.variants.some((v) => v !== bullet.variants[0]);

  function cycle(delta: number) {
    const next = (variantIdx + delta + bullet.variants.length) % bullet.variants.length;
    onChangeSelection({ variantIdx: next });
    setViewingOriginal(false);
    setEditing(false);
  }

  function startEditing() {
    if (viewingOriginal) return;
    setDraft(currentText);
    setEditing(true);
  }

  function commitEdit() {
    setEditing(false);
    if (draft.trim() && draft !== currentText) {
      onChangeSelection({ customText: draft });
    }
  }

  function discardEdit() {
    setEditing(false);
    onChangeSelection({ variantIdx });
  }

  const label = viewingOriginal
    ? "your original wording"
    : isCustom
      ? `your edit, based on ${bullet.source_fact_ids[0]}`
      : hasRealVariants
        ? `rewrite ${variantIdx + 1} of 3 · ${bullet.source_fact_ids[0]}`
        : `your confirmed wording · ${bullet.source_fact_ids[0]}`;

  return (
    <div className="my-1 rounded-[7px] border border-em-softb bg-em-soft p-2.5">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        {onMove && (
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => onMove("up")}
              disabled={!canMoveUp}
              aria-label="Move up"
              className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-ink hover:border-ink disabled:cursor-default disabled:opacity-30 disabled:hover:border-em-softb"
            >
              ↑
            </button>
            <button
              type="button"
              onClick={() => onMove("down")}
              disabled={!canMoveDown}
              aria-label="Move down"
              className="rounded-md border border-em-softb bg-white px-1.5 py-0.5 text-xs text-ink hover:border-ink disabled:cursor-default disabled:opacity-30 disabled:hover:border-em-softb"
            >
              ↓
            </button>
          </div>
        )}
        {hasRealVariants && (
          <>
            <button
              type="button"
              onClick={() => cycle(-1)}
              aria-label="Previous rewrite"
              className="rounded-md border border-em-softb bg-white px-2 py-0.5 text-sm text-ink hover:border-ink"
            >
              ‹
            </button>
            <div className="flex gap-1">
              {bullet.variants.map((_, i) => (
                <span
                  key={i}
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    !isCustom && !viewingOriginal && i === variantIdx
                      ? "bg-em-accent"
                      : "bg-[#d9c9c0]"
                  )}
                />
              ))}
            </div>
            <button
              type="button"
              onClick={() => cycle(1)}
              aria-label="Next rewrite"
              className="rounded-md border border-em-softb bg-white px-2 py-0.5 text-sm text-ink hover:border-ink"
            >
              ›
            </button>
          </>
        )}

        {!editing && (
          <button
            type="button"
            onClick={startEditing}
            disabled={viewingOriginal}
            className="text-xs disabled:cursor-default"
          >
            <span className="font-semibold text-em-deep">{label}</span>{" "}
            <span className="text-ink/50">· click the text to edit</span>
          </button>
        )}

        <div className="ml-auto flex items-center gap-3">
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="text-xs text-red-700 underline hover:text-red-900"
            >
              delete this line
            </button>
          )}
          {showDiscard && (
            <button
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={discardEdit}
              className="text-xs text-em-deep underline hover:text-ink"
            >
              ↺ discard my edit
            </button>
          )}
          <button
            type="button"
            onClick={() => setViewingOriginal((v) => !v)}
            className="text-xs text-em-deep underline hover:text-ink"
          >
            {viewingOriginal
              ? isCustom
                ? "↩ back to my edit"
                : "↩ back to Emend's rewrite"
              : "view my original"}
          </button>
        </div>
      </div>

      {editing && (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commitEdit}
          rows={2}
          autoFocus
          className="mt-2 w-full resize-none rounded-md border border-em-softb bg-white p-2 text-sm text-ink focus:border-em-accent focus:outline-none"
        />
      )}
      {viewingOriginal && (
        <p className="mt-2 text-sm text-ink/70 italic">{originalText}</p>
      )}
    </div>
  );
}
