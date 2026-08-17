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
    pdf_path, log = compile_tex(
        r"\documentclass{article}\begin{document}\undefinedmacro",
        output_dir=tmp_path,
        timeout_s=60,
    )
    assert pdf_path == ""
    assert "error" in log.lower() or "undefined" in log.lower()


def test_missing_tectonic_binary(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    pdf_path, log = compile_tex("anything")
    assert pdf_path == ""
    assert "not found" in log


def test_compile_log_never_leaks_the_real_temp_path(monkeypatch, tmp_path):
    # Tectonic echoes the paths it processed (--outdir, the .tex source)
    # into its own stdout/stderr, and that log is returned verbatim to the
    # client on a failed /finalize -- the server's real temp-directory
    # layout shouldn't ship in an error message. Doesn't require a real
    # tectonic binary: subprocess.run itself is mocked, so this exercises
    # the sanitization regardless of what's installed on this machine.
    import subprocess as subprocess_module

    from latex import compile as compile_module

    monkeypatch.setattr(compile_module.shutil, "which", lambda _: "/usr/bin/tectonic")

    captured_workdir = {}

    def fake_run(cmd, **kwargs):
        workdir = kwargs["cwd"]
        captured_workdir["value"] = workdir
        return subprocess_module.CompletedProcess(
            cmd,
            returncode=1,
            stdout=f"error: unknown macro in {workdir}/resume.tex\n",
            stderr=f"note: see {workdir}/resume.log for details\n",
        )

    monkeypatch.setattr(compile_module.subprocess, "run", fake_run)

    pdf_path, log = compile_tex("anything", timeout_s=60)

    assert pdf_path == ""
    assert captured_workdir["value"] not in log
    assert "<workdir>" in log
