export function KeywordChips({
  matched,
  missing,
}: {
  matched: string[];
  missing: string[];
}) {
  return (
    <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
      {matched.map((keyword) => (
        <span key={keyword} className="rounded bg-em-ok-bg px-2 py-1 text-em-ok-fg">
          {keyword} ✓
        </span>
      ))}
      {missing.map((keyword) => (
        <span
          key={keyword}
          className="rounded bg-em-warn-bg px-2 py-1 text-em-warn-fg line-through"
        >
          {keyword}
        </span>
      ))}
    </div>
  );
}
