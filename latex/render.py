"""Render MasterResume / TailoredResume objects into Jake's-style LaTeX source."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from core.schemas import Experience, MasterResume, Project, TailoredResume, TailoredSection

from .escaping import escape_latex

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    block_start_string=r"\BLOCK{",
    block_end_string="}",
    variable_start_string=r"\VAR{",
    variable_end_string="}",
    comment_start_string=r"\COMMENT{",
    comment_end_string="}",
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    finalize=escape_latex,
    undefined=StrictUndefined,
)


def _experience_row(exp: Experience, bullets: list[str]) -> dict:
    return {
        "title": exp.title,
        "dates": f"{exp.start} -- {exp.end}",
        "company": exp.company,
        "location": exp.location,
        "bullets": bullets,
    }


def _project_row(proj: Project, bullets: list[str]) -> dict:
    return {
        "name": proj.name,
        "tech": ", ".join(proj.tech),
        "bullets": bullets,
    }


def _tailored_rows(
    sections: list[TailoredSection], by_id: dict[str, Experience | Project], kind: str
) -> list:
    rows = []
    for section in sections:
        source = by_id.get(section.ref_id)
        if source is None:
            raise ValueError(f"tailored {kind} section references unknown id {section.ref_id!r}")
        bullets = [b.text for b in section.bullets]
        if isinstance(source, Experience):
            rows.append(_experience_row(source, bullets))
        else:
            rows.append(_project_row(source, bullets))
    return rows


def render_tex(master: MasterResume, tailored: TailoredResume | None) -> str:
    """Render the resume to LaTeX source.

    Refactor mode (tailored=None): every master experience/project renders with its
    own facts as bullets. Tailor mode: only the sections the tailored resume selects
    (by ref_id) render, with tailored bullets substituting the master facts —
    structural fields (company, title, dates, location, tech) always come from
    master, so the tailor can never alter them. Unknown ref_ids raise ValueError.
    """
    if tailored is None:
        experiences = [_experience_row(e, [f.text for f in e.facts]) for e in master.experiences]
        projects = [_project_row(p, [f.text for f in p.facts]) for p in master.projects]
        skills = master.skills
    else:
        exp_by_id: dict[str, Experience | Project] = {e.id: e for e in master.experiences}
        proj_by_id: dict[str, Experience | Project] = {p.id: p for p in master.projects}
        experiences = _tailored_rows(tailored.experiences, exp_by_id, "experience")
        projects = _tailored_rows(tailored.projects, proj_by_id, "project")
        skills = tailored.skills or master.skills

    links = [
        {
            "url": link if link.startswith(("http://", "https://")) else f"https://{link}",
            "display": link.removeprefix("https://").removeprefix("http://"),
        }
        for link in master.links
    ]

    context = {
        "name": master.name,
        "email": master.email,
        "phone": master.phone,
        "links": links,
        "education": master.education,
        "experiences": experiences,
        "projects": projects,
        "skills": skills,
    }
    return _env.get_template("resume.tex.jinja").render(**context)
