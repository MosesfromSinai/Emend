"use client";

import { Button } from "@/components/ui/button";
import { FactTag } from "@/components/ui/fact-tag";
import { Textarea } from "@/components/ui/textarea";
import { nextFactId } from "@/lib/master-resume";
import type { Fact } from "@/lib/types";

// The confirmation unit the brief describes: "render the proposed facts with
// their GA-01-style tags → user edits/confirms each." Every fact here is
// scoped to one section id, matching core's <ENTITY>-<NN> section-prefix rule.
export function FactList({
  sectionId,
  facts,
  onChange,
}: {
  sectionId: string;
  facts: Fact[];
  onChange: (facts: Fact[]) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      {facts.map((fact, index) => (
        <div key={fact.id} className="flex items-start gap-2">
          <FactTag id={fact.id} className="mt-2" />
          <Textarea
            value={fact.text}
            rows={2}
            onChange={(e) => {
              const next = [...facts];
              next[index] = { ...fact, text: e.target.value };
              onChange(next);
            }}
            className="flex-1"
          />
          <button
            type="button"
            aria-label={`Remove fact ${fact.id}`}
            onClick={() => onChange(facts.filter((_, i) => i !== index))}
            className="mt-2 text-ink/40 hover:text-ink"
          >
            ×
          </button>
        </div>
      ))}
      <Button
        type="button"
        variant="ghost"
        className="self-start px-1 py-1"
        onClick={() =>
          onChange([
            ...facts,
            { id: nextFactId(sectionId, facts.map((f) => f.id)), text: "" },
          ])
        }
      >
        + Add fact
      </Button>
    </div>
  );
}
