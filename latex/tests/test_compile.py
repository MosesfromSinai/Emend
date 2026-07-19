from pathlib import Path

from latex import render_and_compile
from latex.compile import compile_tex
from latex.render import render_tex


def test_compile_produces_pdf(master, tmp_path):
    tex = render_tex(master, None)
    pdf_path, log = compile_tex(tex, output_dir=tmp_path, timeout_s=60)
    assert pdf_path, f"compile failed:\n{log}"
    pdf = Path(pdf_path)
    assert pdf.exists()
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_render_and_compile_contract(master, tailored):
    tex, pdf_path, log = render_and_compile(master, tailored)
    assert isinstance(tex, str) and tex.startswith("%")
    assert pdf_path, f"compile failed:\n{log}"
    assert Path(pdf_path).exists()
    assert isinstance(log, str)


def test_invalid_latex_fails_with_surfaced_log(tmp_path):
    pdf_path, log = compile_tex(r"\documentclass{article}\begin{document}\undefinedmacro",
                                output_dir=tmp_path, timeout_s=60)
    assert pdf_path == ""
    assert "error" in log.lower() or "undefined" in log.lower()


def test_missing_tectonic_binary(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    pdf_path, log = compile_tex("anything")
    assert pdf_path == ""
    assert "not found" in log
