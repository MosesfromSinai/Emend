"use client";

// A small circular red X -- the one delete affordance used everywhere
// something can be removed (a bullet, a whole entry). Deletion is implied
// by the icon; no "delete" label needed.
export function DeleteButton({
  onClick,
  label,
}: {
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-red-300 bg-red-50 text-[11px] font-bold leading-none text-red-700 hover:border-red-500 hover:bg-red-100 hover:text-red-900"
    >
      ×
    </button>
  );
}
