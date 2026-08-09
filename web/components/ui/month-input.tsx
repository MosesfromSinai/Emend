import { fromMonthInputValue, toMonthInputValue } from "@/lib/date";
import { cn } from "@/lib/utils";

const FIELD = cn(
  "w-full rounded-md border border-em-softb bg-white px-3 py-2 text-sm text-ink",
  "focus:border-em-accent focus:outline-none focus:ring-1 focus:ring-em-accent"
);

// A resume start/end date is still just a free-text string under the hood
// ("Aug 2021", "Present", ""). This only shapes how a user *enters* one --
// a native month picker instead of a bare text box -- so someone typing a
// start/end date can't land on something like "0821" that a reader can't
// parse. A value already in the field that the picker can't represent (an
// imported "Spring 2021", say) falls back to plain text rather than being
// silently blanked out.
export function MonthInput({
  value,
  onChange,
  placeholder,
  allowPresent,
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  allowPresent?: boolean;
  className?: string;
}) {
  const trimmed = value.trim();
  const isPresent = allowPresent && trimmed.toLowerCase() === "present";
  const monthValue = toMonthInputValue(value);
  const useMonthPicker = !isPresent && (trimmed === "" || monthValue !== "");

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <div className="w-36 shrink-0">
        {isPresent ? (
          <div className={cn(FIELD, "text-em-muted")}>Present</div>
        ) : useMonthPicker ? (
          <input
            type="month"
            className={FIELD}
            value={monthValue}
            onChange={(e) => onChange(fromMonthInputValue(e.target.value))}
          />
        ) : (
          <input
            className={FIELD}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
          />
        )}
      </div>
      {allowPresent && (
        <label className="flex shrink-0 items-center gap-1 text-xs whitespace-nowrap text-em-muted">
          <input
            type="checkbox"
            checked={isPresent}
            onChange={(e) => onChange(e.target.checked ? "Present" : "")}
          />
          Present
        </label>
      )}
    </div>
  );
}
