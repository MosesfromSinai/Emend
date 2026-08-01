import Link from "next/link";
import { Reveal } from "@/components/landing/reveal";

export function CtaBand() {
  return (
    <div className="bg-ink">
      <Reveal className="mx-auto max-w-270 px-8 py-16 text-center">
        <div className="mb-3 font-mono text-[11px] tracking-[.12em] text-em-bright">
          BUILT BY A TEAM OF 4 NEW GRADS WHO GET IT
        </div>
        <h2 className="mb-6 text-[28px] font-semibold text-paper sm:text-[40px]">
          Ready to get started?
        </h2>
        <Link
          href="/app"
          className="inline-block rounded-lg bg-paper px-7 py-3.25 text-[15px] font-semibold text-ink hover:bg-em-softb"
        >
          Tailor your resume
        </Link>
        <p className="mx-auto mt-5 max-w-md text-[13px] text-[#a89f8c]">
          No account needed — your session stays private to your browser for
          as long as you keep it open.
        </p>
      </Reveal>
    </div>
  );
}
