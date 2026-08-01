"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// Editable list of plain strings: links, coursework, project tech, one
// category's skills. Shared so all four don't reinvent add/edit/remove.
export function StringList({
  items,
  onChange,
  placeholder,
  addLabel,
}: {
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  addLabel: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-1">
          <Input
            value={item}
            placeholder={placeholder}
            onChange={(e) => {
              const next = [...items];
              next[index] = e.target.value;
              onChange(next);
            }}
            className="w-auto min-w-[8ch]"
          />
          <button
            type="button"
            aria-label="Remove"
            onClick={() => onChange(items.filter((_, i) => i !== index))}
            className="text-ink/40 hover:text-ink"
          >
            ×
          </button>
        </div>
      ))}
      <Button
        type="button"
        variant="ghost"
        className="px-2 py-1"
        onClick={() => onChange([...items, ""])}
      >
        + {addLabel}
      </Button>
    </div>
  );
}
