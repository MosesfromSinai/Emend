"use client";

import { DeleteButton } from "@/components/ui/delete-button";

export interface OverrideField {
  key: string;
  label?: string;
  value: string;
  // per-field, not per-editor: a composite line like "email | phone | a
  // link" must let someone delete just the phone number, not the whole line
  onDelete?: () => void;
  // Present only when this field is both deletable *and* has a single
  // well-known original to snap back to (the header Name -- unlike a
  // deleted fact/entry, which needs its own restore-chip list since there's
  // no single field for "the" original text). Clicking Delete on a field
  // like this used to blank it with no way back short of retyping it from
  // memory.
  onRestore?: () => void;
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
}: {
  fields: OverrideField[];
  onChange: (key: string, text: string) => void;
}) {
  return (
    <div className="my-1 flex flex-wrap items-center gap-2 rounded-[7px] border border-em-softb bg-em-soft/70 p-2">
      {fields.map((field, i) => (
        <div key={field.key} className="flex min-w-0 flex-1 items-center gap-1.5">
          <input
            value={field.value}
            onChange={(e) => onChange(field.key, e.target.value)}
            placeholder={field.label}
            autoFocus={i === 0}
            className="min-w-0 flex-1 rounded-md border border-em-softb bg-white px-2 py-1 text-sm text-ink focus:border-em-accent focus:outline-none"
          />
          {field.onDelete && (
            <DeleteButton onClick={field.onDelete} label={`Delete ${field.label ?? "this field"}`} />
          )}
          {field.onRestore && (
            <button
              type="button"
              onClick={field.onRestore}
              className="shrink-0 text-xs font-medium text-em-accent hover:underline"
            >
              Restore
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
