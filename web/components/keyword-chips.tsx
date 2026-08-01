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
        <span key={keyword} className="rounded bg-[#eef0e2] px-2 py-1 text-[#5a6a34]">
          {keyword} ✓
        </span>
      ))}
      {missing.map((keyword) => (
        <span
          key={keyword}
          className="rounded bg-[#f4e6e2] px-2 py-1 text-[#9a4a34] line-through"
        >
          {keyword}
        </span>
      ))}
    </div>
  );
}
