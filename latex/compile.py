"""Sandboxed Tectonic compilation: --untrusted, hard timeout, CPU/memory rlimits."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    import resource
except ImportError:  # non-POSIX
    resource = None

DEFAULT_TIMEOUT_S = int(os.environ.get("COMPILE_TIMEOUT_SECONDS", "10"))
_CPU_LIMIT_S = 30
_MEMORY_LIMIT_BYTES = 1024 * 1024 * 1024  # 1 GiB address space


def _set_rlimits() -> None:
    if resource is None:
        return
    for limit, value in (
        (resource.RLIMIT_CPU, _CPU_LIMIT_S),
        (resource.RLIMIT_AS, _MEMORY_LIMIT_BYTES),
    ):
        try:
            resource.setrlimit(limit, (value, value))
        except (ValueError, OSError):
            # e.g. macOS rejects RLIMIT_AS; never abort the spawn over a cap
            pass


def compile_tex(
    tex: str, output_dir: str | Path | None = None, timeout_s: int = DEFAULT_TIMEOUT_S
) -> tuple[str, str]:
    """Compile LaTeX source with Tectonic in untrusted mode.

    Returns (pdf_path, log). On failure pdf_path is "" and the log explains why —
    this function never raises for compile failures or timeouts.
    """
    tectonic = shutil.which("tectonic")
    if tectonic is None:
        return "", "tectonic binary not found on PATH"

    with tempfile.TemporaryDirectory(prefix="emend-compile-") as workdir:
        tex_file = Path(workdir) / "resume.tex"
        tex_file.write_text(tex, encoding="utf-8")
        env = {**os.environ, "TECTONIC_UNTRUSTED_MODE": "1"}
        cmd = [tectonic, "--untrusted"]
        if os.environ.get("TECTONIC_ONLY_CACHED"):
            cmd.append("--only-cached")
        cmd += ["--outdir", workdir, str(tex_file)]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                preexec_fn=_set_rlimits if resource is not None else None,
                env=env,
                cwd=workdir,
            )
        except subprocess.TimeoutExpired:
            return "", f"compile timed out after {timeout_s}s"

        log = f"{proc.stdout}\n{proc.stderr}".strip()
        if proc.returncode != 0:
            return "", log or f"tectonic exited with code {proc.returncode}"

        built_pdf = Path(workdir) / "resume.pdf"
        if not built_pdf.exists():
            return "", f"tectonic reported success but produced no PDF\n{log}"

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="emend-artifact-")
        dest_dir = Path(output_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = dest_dir / "resume.pdf"
        shutil.copyfile(built_pdf, pdf_path)
        return str(pdf_path), log
