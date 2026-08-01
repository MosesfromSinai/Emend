"use client";

import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

// The api serves artifacts session-scoped: withCredentials sends the httpOnly
// cookie on pdf.js's own fetch, which react-pdf's plain `file={url}` form
// does not do on its own. react-pdf docs say to keep this options object
// stable across renders, hence the module-level constant.
const PDF_OPTIONS = { withCredentials: true };

export function PdfViewer({ url }: { url: string }) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex justify-center overflow-auto bg-[#eceadf] p-6">
      <Document
        file={url}
        options={PDF_OPTIONS}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
        onLoadError={() => setError("Couldn't load the PDF.")}
        loading={<p className="text-sm text-ink/60">Loading PDF…</p>}
      >
        {error && <p className="text-sm text-red-700">{error}</p>}
        {Array.from({ length: numPages ?? 0 }, (_, i) => (
          <Page
            key={i}
            pageNumber={i + 1}
            width={480}
            className="mb-4 shadow-lg last:mb-0"
          />
        ))}
      </Document>
    </div>
  );
}
