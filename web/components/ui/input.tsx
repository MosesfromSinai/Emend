import { type InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-md border border-em-softb bg-white px-3 py-2 text-sm text-ink",
        "focus:border-em-accent focus:outline-none focus:ring-1 focus:ring-em-accent",
        className
      )}
      {...props}
    />
  );
}
