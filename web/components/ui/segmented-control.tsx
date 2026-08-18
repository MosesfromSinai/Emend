import { cn } from "@/lib/utils";

// A rounded --em-soft track with the active option raised as a white pill;
// inactive options sit flush in the track. Shared by Tailor's mode switch
// and Export's Resume/LaTeX toggle.
export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: string }[];
}) {
  return (
    <div role="radiogroup" className="inline-flex w-fit rounded-full bg-em-soft p-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
            value === option.value
              ? "bg-white text-ink shadow-sm"
              : "text-ink/60 hover:text-ink"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
