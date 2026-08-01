"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

// Rendered verbatim — the `% grounded:` receipts are the product, per the
// brief: no stripping, no reformatting.
export function TexPane({ tex }: { tex: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(tex);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex h-full flex-col bg-code-pane">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
        <span className="font-mono text-xs text-white/60">resume.tex</span>
        <Button variant="ghost" className="px-2 py-1 text-em-bright" onClick={copy}>
          {copied ? "Copied ✓" : "Copy .tex"}
        </Button>
      </div>
      <pre className="flex-1 overflow-auto p-4 font-mono text-xs leading-relaxed text-white/85">
        {tex}
      </pre>
    </div>
  );
}
