"use client";

import { useState } from "react";

// A minimal click-to-edit control for non-fact-backed text (coursework,
// skills, header fields, structural entry fields) -- no variants/original
// to cycle through, just a free-text override. Sibling to RewriteBar, which
// handles the fact-grounded case.
export function OverrideEditor({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (text: string) => void;
}) {
  const [draft, setDraft] = useState(value);

  function commit() {
    if (draft !== value) onChange(draft);
  }

  return (
    <div className="my-1 rounded-[7px] border border-em-softb bg-em-soft p-2.5">
      <div className="mb-1 text-xs font-semibold text-em-deep">{label}</div>
      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        rows={2}
        autoFocus
        className="w-full resize-none rounded-md border border-em-softb bg-white p-2 text-sm text-ink focus:border-em-accent focus:outline-none"
      />
    </div>
  );
}
