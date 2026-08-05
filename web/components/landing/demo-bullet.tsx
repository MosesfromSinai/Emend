"use client";

import type { BulletState } from "@/lib/use-sentence-demo";
import type { DemoBullet } from "@/lib/demo-persona";
import { cn } from "@/lib/utils";

export function DemoBulletRow({
  bulletKey,
  bullet,
  state,
  selected,
  onSelect,
  onPatch,
}: {
  bulletKey: string;
  bullet: DemoBullet;
  state: BulletState;
  selected: boolean;
  onSelect: () => void;
  onPatch: (next: Partial<BulletState>) => void;
}) {
  const hasCustom = state.custom != null;
  const variant = bullet.variants[state.idx];
  const shown = state.orig ? bullet.original : hasCustom ? state.custom! : variant.text;
  // forces the span to remount (and pick up `shown`) whenever we
  // programmatically change what's displayed — see use-sentence-demo.ts
  const textKey = `${bulletKey}:${state.idx}:${state.orig ? "o" : "r"}:${hasCustom ? "c" + state.custom!.length : "n"}:${state.rev}`;

  return (
    <div>
      <div
        data-demo-interactive
        onClick={(e) => {
          e.stopPropagation();
          if (!selected) onSelect();
        }}
        className={cn(
          "-mx-2 flex cursor-pointer items-baseline gap-2 rounded-md px-2 py-1 transition-colors",
          selected ? "bg-em-soft" : "hover:bg-em-soft"
        )}
      >
        <span className="text-[12.5px] text-[#444]">•</span>
        <span
          key={textKey}
          contentEditable={selected}
          suppressContentEditableWarning
          spellCheck={false}
          onBlur={(e) => {
            const text = e.currentTarget.textContent?.trim() ?? "";
            if (text && text !== shown) {
              onPatch({ custom: text, orig: false, dirty: false });
            } else {
              if (!text) e.currentTarget.textContent = shown;
              onPatch({ dirty: false });
            }
          }}
          onInput={() => {
            if (!state.dirty) onPatch({ dirty: true });
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              e.currentTarget.blur();
            }
          }}
          className="flex-1 text-[13px] leading-relaxed text-[#333] outline-none"
        >
          {shown}
        </span>
        <span className="shrink-0 font-mono text-[9.5px] font-semibold text-em-accent">
          {state.orig ? "original" : hasCustom ? "edited ✎" : `% ${bullet.source}`}
        </span>
      </div>
      {selected && (
        <DemoBulletToolbar bullet={bullet} state={state} onPatch={onPatch} />
      )}
    </div>
  );
}

function DemoBulletToolbar({
  bullet,
  state,
  onPatch,
}: {
  bullet: DemoBullet;
  state: BulletState;
  onPatch: (next: Partial<BulletState>) => void;
}) {
  const hasCustom = state.custom != null;
  // shows the moment typing starts, not just after blur saves it -- dirty
  // covers the in-progress keystroke, hasCustom covers the saved edit
  const showDiscard = state.dirty || hasCustom;
  const cycle = (delta: 1 | -1) =>
    onPatch({ idx: (state.idx + delta + 3) % 3, orig: false, custom: null, dirty: false, rev: state.rev + 1 });

  const modeLabel = state.orig
    ? "your original wording"
    : hasCustom
      ? `your edit · based on fact ${bullet.source}`
      : `rewrite ${state.idx + 1} of 3 · fact ${bullet.source}`;

  const origBtnLabel = state.orig
    ? hasCustom
      ? "↩ back to my edit"
      : "↩ back to Emend's rewrite"
    : "view my original";

  return (
    <div
      data-demo-interactive
      onClick={(e) => e.stopPropagation()}
      className="my-1.5 flex flex-wrap items-center gap-2.5 rounded-lg bg-code-pane px-3 py-2.5"
    >
      <button
        onClick={() => cycle(-1)}
        className="h-7 w-7 rounded-md border border-[#4a463c] text-sm font-semibold text-paper hover:border-em-bright hover:text-em-bright"
      >
        ‹
      </button>
      <div className="flex gap-1.5">
        {bullet.variants.map((_, i) =>
          state.orig ? (
            // hollow, not filled: signals "no rewrite active" rather than
            // reading as three identical (and seemingly broken) dots
            <span
              key={i}
              className="h-1.5 w-1.5 rounded-full border border-[#4a463c]"
            />
          ) : (
            <span
              key={i}
              className="h-1.5 w-1.5 rounded-full"
              style={{ background: !hasCustom && i === state.idx ? "var(--em-bright)" : "#4a463c" }}
            />
          )
        )}
      </div>
      <button
        onClick={() => cycle(1)}
        className="h-7 w-7 rounded-md border border-[#4a463c] text-sm font-semibold text-paper hover:border-em-bright hover:text-em-bright"
      >
        ›
      </button>
      <span className="text-[11px] text-[#a89f8c]">{modeLabel}</span>
      <span className="text-[10.5px] text-[#8f887a]">
        · click text to edit · your words are kept
      </span>
      {showDiscard && (
        <button
          onClick={() => onPatch({ custom: null, orig: false, dirty: false, rev: state.rev + 1 })}
          className="rounded px-1.5 py-1 text-[11.5px] font-semibold whitespace-nowrap text-[#a89f8c] hover:bg-em-ink-2 hover:text-paper"
        >
          ↺ discard my edit
        </button>
      )}
      <button
        onClick={() => onPatch({ orig: !state.orig })}
        className="ml-auto rounded px-1.5 py-1 text-[11.5px] font-semibold whitespace-nowrap text-em-bright hover:bg-em-ink-2"
      >
        {origBtnLabel}
      </button>
    </div>
  );
}
