import Link from "next/link";

export const metadata = {
  title: "Privacy — Emend",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <Link href="/" className="text-[12.5px] font-medium text-ink/60 hover:text-ink">
        ← Back to home
      </Link>
      <h1 className="mt-4 mb-6 font-serif text-3xl font-semibold">Privacy</h1>
      <div className="flex flex-col gap-5 text-sm leading-relaxed text-ink/80">
        <p>
          Emend doesn&apos;t have accounts or logins. When you visit, the app issues
          your browser a private, random session cookie — that cookie is the only
          thing tying your resume and applications to you. It lasts up to a year
          unless you clear it or delete your data (see below).
        </p>
        <p>
          <strong className="text-ink">What&apos;s stored:</strong>{" "}
          the resume facts you confirm, any job postings you paste or link to
          tailor against, and the resumes/PDFs Emend generates for you. Nothing
          is shared with other visitors, and nothing is sold.
        </p>
        <p>
          <strong className="text-ink">Where it goes:</strong>{" "}
          when you tailor a resume, your confirmed facts and the job posting
          text are sent to Anthropic&apos;s Claude API to generate and check
          the rewritten bullets. That request is processed to produce your
          result — it&apos;s not used to train Emend, and Emend doesn&apos;t
          control Anthropic&apos;s own retention policy for API requests.
        </p>
        <p>
          <strong className="text-ink">Deleting your data:</strong>{" "}
          click &quot;Delete my data&quot; in the app header at any time. This
          permanently removes your confirmed resume, every application
          you&apos;ve tailored, and their exported files — there&apos;s no
          undo, and no account to keep it under.
        </p>
        <p>This is a small, solo-built app — this page will grow if the app does.</p>
      </div>
    </main>
  );
}
