export function KeywordChips({
  matched,
  missing,
}: {
  matched: string[];
  missing: string[];
}) {
  return (
    <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
      {matched.map((keyword, i) => (
        // Index joined in, not just the keyword: matched_keywords is a
        // plain list[str] with no schema-level uniqueness guarantee, so a
        // duplicate string from the backend would otherwise collide as a
        // React key.
        <span key={`${keyword}-${i}`} className="rounded bg-em-ok-bg px-2 py-1 text-em-ok-fg">
          {keyword} ✓
        </span>
      ))}
      {missing.map((keyword, i) => (
        <span
          key={`${keyword}-${i}`}
          className="rounded bg-em-warn-bg px-2 py-1 text-em-warn-fg line-through"
        >
          {keyword}
        </span>
      ))}
    </div>
  );
}
