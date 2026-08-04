"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";
import type { BulletSelection, TailoredBullet } from "@/lib/types";

// Parent must pass `key={factId}` -- a fresh instance per bullet is how
// editing/preview state resets when the active bullet changes, instead of
// an effect that would fire a synchronous setState on every switch.
export function RewriteBar({
  bullet,
  selection,
  originalText,
  onChangeSelection,
  onClose,
}: {
  bullet: TailoredBullet;
  selection?: BulletSelection;
  originalText: string;
  onChangeSelection: (selection: BulletSelection) => void;
  onClose: () => void;
}) {
  const [viewingOriginal, setViewingOriginal] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  const variantIdx = selection?.variantIdx ?? 0;
  const isCustom = Boolean(selection?.customText);
  const currentText = selection?.customText ?? bullet.variants[variantIdx];

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
    setDraft(currentText);
    onChangeSelection({ variantIdx });
    setEditing(false);
  }

  const label = viewingOriginal
    ? "your original wording"
    : isCustom
      ? `your edit, based on ${bullet.source_fact_ids[0]}`
      : `rewrite ${variantIdx + 1} of 3 · ${bullet.source_fact_ids[0]}`;

  return (
    <div className="rounded-xl bg-ink p-4 text-paper">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => cycle(-1)}
            aria-label="Previous rewrite"
            className="rounded-md px-2 py-1 text-sm hover:bg-white/10"
          >
            ‹
          </button>
          <div className="flex gap-1">
            {bullet.variants.map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  !isCustom && !viewingOriginal && i === variantIdx ? "bg-em-bright" : "bg-paper/25"
                )}
              />
            ))}
          </div>
          <button
            type="button"
            onClick={() => cycle(1)}
            aria-label="Next rewrite"
            className="rounded-md px-2 py-1 text-sm hover:bg-white/10"
          >
            ›
          </button>
          <span className="ml-1 font-mono text-xs text-paper/70">{label}</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setViewingOriginal((v) => !v)}
            className="text-xs text-paper/70 underline hover:text-paper"
          >
            {viewingOriginal
              ? isCustom
                ? "↩ back to my edit"
                : "↩ back to Emend's rewrite"
              : "view my original"}
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-paper/50 hover:text-paper"
          >
            ✕
          </button>
        </div>
      </div>

      {editing ? (
        <div className="mt-3">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commitEdit}
            rows={3}
            autoFocus
            className="w-full resize-none rounded-md bg-white/10 p-2.5 text-sm text-paper focus:outline-none"
          />
          {draft !== currentText && (
            <button
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={discardEdit}
              className="mt-1.5 text-xs text-paper/60 underline hover:text-paper"
            >
              ↺ discard my edit
            </button>
          )}
        </div>
      ) : (
        <p
          onClick={startEditing}
          className={cn(
            "mt-3 text-sm text-paper/90",
            !viewingOriginal && "cursor-text hover:text-paper"
          )}
        >
          {viewingOriginal ? originalText : currentText}
        </p>
      )}
    </div>
  );
}
