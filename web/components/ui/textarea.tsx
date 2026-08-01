import { type TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Textarea({
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full rounded-md border border-em-softb bg-white px-3 py-2 font-mono text-sm text-ink",
        "focus:border-em-accent focus:outline-none focus:ring-1 focus:ring-em-accent",
        className
      )}
      {...props}
    />
  );
}
