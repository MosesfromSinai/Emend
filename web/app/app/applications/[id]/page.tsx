"use client";

import { use } from "react";

import { GroundedPill } from "@/components/grounded-pill";
import { KeywordChips } from "@/components/keyword-chips";
import { MatchScoreRing } from "@/components/match-score-ring";
import { PdfViewer } from "@/components/pdf-viewer";
import { ProvenancePanel } from "@/components/provenance-panel";
import { TexPane } from "@/components/tex-pane";
import { Button } from "@/components/ui/button";
import { artifactUrl } from "@/lib/api";
import { usePollApplication } from "@/lib/use-poll-application";

export default function ApplicationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { application, error } = usePollApplication(id);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!application) return <p className="text-sm text-ink/60">Loading…</p>;

  if (application.status === "queued" || application.status === "running") {
    return (
      <div className="flex flex-col items-center gap-2 py-16 text-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-em-softb border-t-em-accent" />
        <p className="text-sm text-ink/70">
          {application.status === "queued" ? "Queued…" : "Typesetting your resume…"}
        </p>
      </div>
    );
  }

  if (application.status === "failed") {
    return (
      <div className="flex flex-col gap-3">
        <h1 className="font-serif text-xl font-semibold text-red-800">
          This one didn&apos;t go through.
        </h1>
        <pre className="overflow-auto whitespace-pre-wrap rounded-md bg-code-pane p-4 text-xs text-white/85">
          {application.error ?? "No error detail was recorded."}
        </pre>
      </div>
    );
  }

  const { version } = application;
  if (!version) {
    return <p className="text-sm text-ink/60">Done, but no artifact was recorded.</p>;
  }

  const report = version.report;

  return (
    <div className="flex flex-col gap-5">
      {report && (
        <div className="flex flex-wrap items-center gap-4 rounded-lg border border-em-softb p-4">
          <MatchScoreRing score={report.match_score} />
          <KeywordChips matched={report.matched_keywords} missing={report.missing_keywords} />
          <GroundedPill
            supportedCount={report.verdicts.filter((v) => v.supported).length}
            total={report.verdicts.length}
          />
        </div>
      )}

      <div className="flex gap-2">
        <Button onClick={() => window.open(artifactUrl(version.pdf_url), "_blank")}>
          Download PDF
        </Button>
        <Button
          variant="secondary"
          onClick={() => window.open(artifactUrl(version.tex_url), "_blank")}
        >
          Download .tex
        </Button>
      </div>

      <div className="grid h-[70vh] grid-cols-2 overflow-hidden rounded-lg border border-em-softb">
        <PdfViewer url={artifactUrl(version.pdf_url)} />
        <TexPane tex={version.tex} />
      </div>

      {report && <ProvenancePanel verdicts={report.verdicts} />}
    </div>
  );
}
