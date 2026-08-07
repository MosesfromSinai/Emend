"use client";

import { DeleteButton } from "@/components/ui/delete-button";

export interface OverrideField {
  key: string;
  label?: string;
  value: string;
}

// The click-to-edit control for non-fact-backed text (coursework, skills,
// header fields, structural entry fields) -- no variants/original to cycle
// through, just free-text. Sibling to RewriteBar, which handles the
// fact-grounded case. A "line" on the resume can back more than one
// text_overrides key (e.g. "company — location" is one visual line, two
// fields), so this takes a list rather than a single value.
export function OverrideEditor({
  fields,
  onChange,
  onDelete,
}: {
  fields: OverrideField[];
  onChange: (key: string, text: string) => void;
  onDelete?: () => void;
}) {
  return (
    <div className="my-1 flex items-center gap-2 rounded-[7px] border border-em-softb bg-em-soft/70 p-2">
      <div className="flex flex-1 flex-wrap items-center gap-2">
        {fields.map((field, i) => (
          <input
            key={field.key}
            value={field.value}
            onChange={(e) => onChange(field.key, e.target.value)}
            placeholder={field.label}
            autoFocus={i === 0}
            className="min-w-0 flex-1 rounded-md border border-em-softb bg-white px-2 py-1 text-sm text-ink focus:border-em-accent focus:outline-none"
          />
        ))}
      </div>
      {onDelete && <DeleteButton onClick={onDelete} label="Delete this line" />}
    </div>
  );
}
