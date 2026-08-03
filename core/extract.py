"""PDF text extraction for the resume-import path.

Pure Python (pypdf), offline, no network, no web/DB imports — core stays
importable and testable without any of the other workflows.
"""

import io

from pypdf import PdfReader

from core.normalize import unwrap_text

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 10
MIN_TEXT_LAYER_CHARS = 200


class PdfExtractionError(ValueError):
    """Raised when a PDF can't be turned into resume text."""


def pdf_to_text(data: bytes) -> str:
    """Extract and unwrap the text layer of a resume PDF."""
    if len(data) > MAX_PDF_BYTES:
        raise PdfExtractionError(f"PDF exceeds {MAX_PDF_BYTES} bytes")
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise PdfExtractionError("could not read PDF") from exc
    if reader.is_encrypted:
        raise PdfExtractionError("PDF is encrypted")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise PdfExtractionError(f"PDF exceeds {MAX_PDF_PAGES} pages")

    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(page for page in pages if page)
    if len(text) < MIN_TEXT_LAYER_CHARS:
        raise PdfExtractionError(
            "PDF has no usable text layer (image-only scan is not OCR'd)"
        )
    return unwrap_text(text)
