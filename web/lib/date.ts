const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

// "Aug 2021" / "August 2021" -> "2021-08" for an <input type="month"> value;
// "" if the display string isn't in a month-year shape the picker can drive.
export function toMonthInputValue(display: string): string {
  const match = display.trim().match(/^([A-Za-z]+)\.?\s+(\d{4})$/);
  if (!match) return "";
  const monthIndex = MONTH_NAMES.findIndex(
    (m) => m.toLowerCase() === match[1].slice(0, 3).toLowerCase()
  );
  if (monthIndex === -1) return "";
  return `${match[2]}-${String(monthIndex + 1).padStart(2, "0")}`;
}

// "2021-08" -> "Aug 2021"
export function fromMonthInputValue(monthValue: string): string {
  const match = monthValue.match(/^(\d{4})-(\d{2})$/);
  if (!match) return "";
  const name = MONTH_NAMES[Number(match[2]) - 1];
  return name ? `${name} ${match[1]}` : "";
}
