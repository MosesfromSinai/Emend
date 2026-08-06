"""Render MasterResume / TailoredResume objects into Jake's-style LaTeX source."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from core.schemas import (
    Experience,
    MasterResume,
    Project,
    TailoredResume,
    TailoredSection,
)

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


def _grounding_comment(ids: list[str]) -> str:
    # Ids land inside a % comment, which runs to end-of-line: collapse any
    # whitespace (esp. newlines) so a hostile id can never terminate the
    # comment and leak content into the document body.
    return ", ".join(" ".join(i.split()) for i in ids)


def _bullet_row(text: str, source_ids: list[str]) -> dict:
    return {"text": text, "grounded": _grounding_comment(source_ids)}


def _experience_row(exp: Experience, bullets: list[dict]) -> dict:
    return {
        "title": exp.title,
        "dates": f"{exp.start} -- {exp.end}",
        "company": exp.company,
        "location": exp.location,
        "bullets": bullets,
    }


def _project_row(proj: Project, bullets: list[dict]) -> dict:
    return {
        "name": proj.name,
        "tech": ", ".join(proj.tech),
        "bullets": bullets,
    }


def _resolve_variant(bullet, selections: dict[str, dict] | None) -> str:
    """Which of a bullet's 3 variants (or a user edit) actually renders.

    Keyed by the bullet's first cited fact -- in practice a bullet almost
    always cites exactly one, and Export's per-line picker treats a bullet
    as one unit regardless. No selection for it: the first variant.
    """
    sel = selections.get(bullet.source_fact_ids[0]) if selections else None
    if not sel:
        return bullet.variants[0]
    custom = sel.get("custom_text")
    if custom:
        return custom
    return bullet.variants[sel.get("variant_idx", 0)]


def _reorder_by_key(items: list, order: list[str] | None, key) -> list:
    """Reorder `items` to match `order` (a list of `key(item)` values).

    Items whose key isn't in `order` keep their relative position, appended
    after the ordered ones -- a stale order (referencing a fact id that's
    since been deleted) or a partial one (missing a newly added fact) can
    never silently drop a bullet.
    """
    if not order:
        return items
    by_key = {key(item): item for item in items}
    ordered = [by_key[k] for k in order if k in by_key]
    seen = set(order)
    ordered.extend(item for item in items if key(item) not in seen)
    return ordered


def _tailored_rows(
    sections: list[TailoredSection],
    by_id: dict[str, Experience | Project],
    kind: str,
    selections: dict[str, dict] | None = None,
    fact_order: dict[str, list[str]] | None = None,
) -> list:
    rows = []
    for section in sections:
        source = by_id.get(section.ref_id)
        if source is None:
            raise ValueError(
                f"tailored {kind} section references unknown id {section.ref_id!r}"
            )
        ordered_bullets = _reorder_by_key(
            section.bullets,
            (fact_order or {}).get(section.ref_id),
            lambda b: b.source_fact_ids[0],
        )
        bullets = [
            _bullet_row(_resolve_variant(b, selections), b.source_fact_ids)
            for b in ordered_bullets
        ]
        if isinstance(source, Experience):
            rows.append(_experience_row(source, bullets))
        else:
            rows.append(_project_row(source, bullets))
    return rows


def render_tex(
    master: MasterResume,
    tailored: TailoredResume | None,
    selections: dict[str, dict] | None = None,
    fact_order: dict[str, list[str]] | None = None,
) -> str:
    """Render the resume to LaTeX source.

    Refactor mode (tailored=None): every master experience/project renders with its
    own facts as bullets. Tailor mode: only the sections the tailored resume selects
    (by ref_id) render, with tailored bullets substituting the master facts —
    structural fields (company, title, dates, location, tech) always come from
    master, so the tailor can never alter them. Unknown ref_ids raise ValueError.

    Each tailored bullet carries 3 grounded variants; `selections` (keyed by
    fact id) picks which one renders -- `{"variant_idx": 1}` or
    `{"custom_text": "..."}` for a user's own edit. No entry for a bullet:
    its first variant renders. Ignored in refactor mode (nothing to pick between).

    `fact_order` (keyed by an experience/project's own id) reorders that
    entry's bullets before rendering -- see `_reorder_by_key`. No entry for
    an id: bullets render in their existing order.

    Every fact-backed bullet is preceded by a "% grounded: <fact ids>" receipt
    comment — the bullet's source_fact_ids in tailor mode, the fact's own id in
    refactor mode. Coursework and skills carry no receipts: they are confirmed
    master data with no fact ids in the contract, not generated content. A bullet
    with empty source_fact_ids renders an empty receipt; rejecting sourceless
    bullets is the upstream validator's job.
    """
    if tailored is None:
        experiences = [
            _experience_row(
                e,
                [
                    _bullet_row(f.text, [f.id])
                    for f in _reorder_by_key(e.facts, (fact_order or {}).get(e.id), lambda f: f.id)
                ],
            )
            for e in master.experiences
        ]
        projects = [
            _project_row(
                p,
                [
                    _bullet_row(f.text, [f.id])
                    for f in _reorder_by_key(p.facts, (fact_order or {}).get(p.id), lambda f: f.id)
                ],
            )
            for p in master.projects
        ]
        skills = master.skills
    else:
        exp_by_id: dict[str, Experience | Project] = {
            e.id: e for e in master.experiences
        }
        proj_by_id: dict[str, Experience | Project] = {p.id: p for p in master.projects}
        experiences = _tailored_rows(
            tailored.experiences, exp_by_id, "experience", selections, fact_order
        )
        projects = _tailored_rows(
            tailored.projects, proj_by_id, "project", selections, fact_order
        )
        skills = tailored.skills

    links = [
        {
            "url": (
                link if link.startswith(("http://", "https://")) else f"https://{link}"
            ),
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
