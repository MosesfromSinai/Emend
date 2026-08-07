from core.schemas import MasterResume, TailoredResume

from .compile import compile_tex
from .render import render_tex

__all__ = ["render_and_compile"]


def render_and_compile(
    master: MasterResume,
    tailored: TailoredResume | None,
    selections: dict[str, dict] | None = None,
    fact_order: dict[str, list[str]] | None = None,
    experience_order: list[str] | None = None,
    project_order: list[str] | None = None,
    section_order: list[str] | None = None,
    excluded_facts: list[str] | None = None,
    excluded_experiences: list[str] | None = None,
    excluded_projects: list[str] | None = None,
    text_overrides: dict[str, str] | None = None,
) -> tuple[str, str, str]:
    """Render to .tex and compile to PDF. Returns (tex, pdf_path, log).

    pdf_path is "" when compilation fails; the log always explains the failure.
    `selections` picks which of a bullet's 3 variants renders, `fact_order`
    reorders bullets within an entry, `experience_order`/`project_order`
    reorder the entries themselves, `section_order` reorders the four
    top-level sections, `excluded_*` drop bullets/entries entirely,
    `text_overrides` free-text edits any non-fact-backed field -- see
    render_tex.
    """
    tex = render_tex(
        master,
        tailored,
        selections=selections,
        fact_order=fact_order,
        experience_order=experience_order,
        project_order=project_order,
        section_order=section_order,
        excluded_facts=excluded_facts,
        excluded_experiences=excluded_experiences,
        excluded_projects=excluded_projects,
        text_overrides=text_overrides,
    )
    pdf_path, log = compile_tex(tex)
    return tex, pdf_path, log
