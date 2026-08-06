from core.schemas import MasterResume, TailoredResume

from .compile import compile_tex
from .render import render_tex

__all__ = ["render_and_compile"]


def render_and_compile(
    master: MasterResume,
    tailored: TailoredResume | None,
    selections: dict[str, dict] | None = None,
    fact_order: dict[str, list[str]] | None = None,
) -> tuple[str, str, str]:
    """Render to .tex and compile to PDF. Returns (tex, pdf_path, log).

    pdf_path is "" when compilation fails; the log always explains the failure.
    `selections` picks which of a bullet's 3 variants renders, `fact_order`
    reorders bullets within an entry -- see render_tex.
    """
    tex = render_tex(master, tailored, selections, fact_order)
    pdf_path, log = compile_tex(tex)
    return tex, pdf_path, log
