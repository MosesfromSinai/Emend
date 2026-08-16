from pathlib import Path

import pytest

from core.extract import MAX_PDF_BYTES, PdfExtractionError, pdf_to_text

PDF_FIXTURES = Path(__file__).parent.parent / "fixtures" / "pdfs"


def _read(name: str) -> bytes:
    return (PDF_FIXTURES / name).read_bytes()


def test_extracts_text_from_a_real_pdf():
    text = pdf_to_text(_read("sample_resume.pdf"))

    assert "Jordan Rivera" in text
    assert "Bright Path Robotics" in text
    assert "pytest integration tests" in text


def test_rejects_oversized_bytes():
    with pytest.raises(PdfExtractionError, match="exceeds"):
        pdf_to_text(b"x" * (MAX_PDF_BYTES + 1))


def test_rejects_encrypted_pdf():
    with pytest.raises(PdfExtractionError, match="encrypted"):
        pdf_to_text(_read("encrypted.pdf"))


def test_rejects_too_many_pages():
    with pytest.raises(PdfExtractionError, match="pages"):
        pdf_to_text(_read("too_many_pages.pdf"))


def test_rejects_thin_text_layer():
    with pytest.raises(PdfExtractionError, match="text layer"):
        pdf_to_text(_read("short_text.pdf"))


def test_rejects_unparseable_bytes():
    with pytest.raises(PdfExtractionError, match="could not read"):
        pdf_to_text(b"not a pdf at all")


def test_wraps_a_page_level_extraction_failure(monkeypatch):
    # A crafted-but-parseable PDF can fail well past PdfReader() construction
    # -- during page-tree traversal or content-stream decoding -- and that
    # used to surface as an unhandled pypdf exception instead of the same
    # clean PdfExtractionError every other bad-PDF case gets.
    from pypdf._page import PageObject

    def broken_extract_text(self, *args, **kwargs):
        raise RuntimeError("corrupt content stream")

    monkeypatch.setattr(PageObject, "extract_text", broken_extract_text)
    with pytest.raises(PdfExtractionError, match="could not read"):
        pdf_to_text(_read("sample_resume.pdf"))
