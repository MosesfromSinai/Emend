"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type TexLine = { text: string; factIds: string[] };

const GROUNDED_RE = /^%\s*grounded:\s*(.+)$/;

// A "% grounded: ID1, ID2" comment always precedes exactly one bullet line
// (render_tex's contract) -- tag the comment and the line right after it
// with the same fact ids, so hovering either highlights the whole receipt.
function parseLines(tex: string): TexLine[] {
  const lines: TexLine[] = [];
  let pending: string[] = [];
  for (const raw of tex.split("\n")) {
    const match = GROUNDED_RE.exec(raw.trim());
    if (match) {
      pending = match[1].split(",").map((id) => id.trim()).filter(Boolean);
      lines.push({ text: raw, factIds: pending });
      continue;
    }
    if (pending.length && raw.trim()) {
      lines.push({ text: raw, factIds: pending });
      pending = [];
    } else {
      lines.push({ text: raw, factIds: [] });
    }
  }
  return lines;
}

function lineClass(text: string): string {
  const trimmed = text.trim();
  if (trimmed.startsWith("%")) return "text-white/40";
  if (trimmed.startsWith("\\")) return "text-em-bright";
  return "text-white/85";
}

// Rendered verbatim — the `% grounded:` receipts are the product, per the
// brief: no stripping, no reformatting.
export function TexPane({
  tex,
  hoveredFactId,
  onHoverFactId,
}: {
  tex: string;
  hoveredFactId?: string | null;
  onHoverFactId?: (id: string | null) => void;
}) {
  const [copied, setCopied] = useState(false);
  const lines = parseLines(tex);

  async function copy() {
    await navigator.clipboard.writeText(tex);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex h-full flex-col bg-[#4a2823]">
      <div className="flex items-center justify-between border-b border-white/10 bg-[#5e352c] px-4 py-2">
        <span className="font-mono text-xs text-white/60">resume.tex</span>
        <Button variant="ghost" className="px-2 py-1 text-em-bright" onClick={copy}>
          {copied ? "Copied ✓" : "Copy .tex"}
        </Button>
      </div>
      <div className="flex-1 overflow-auto py-2 font-mono text-xs leading-[1.85]">
        {lines.map((line, i) => (
          <div
            key={i}
            onMouseEnter={() => line.factIds[0] && onHoverFactId?.(line.factIds[0])}
            onMouseLeave={() => line.factIds.length > 0 && onHoverFactId?.(null)}
            className={cn(
              "flex gap-3 px-3",
              hoveredFactId != null && line.factIds.includes(hoveredFactId) && "bg-white/10"
            )}
          >
            <span className="w-6.5 shrink-0 select-none text-right text-white/25">{i + 1}</span>
            <span className={cn("whitespace-pre-wrap break-all", lineClass(line.text))}>
              {line.text || " "}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
