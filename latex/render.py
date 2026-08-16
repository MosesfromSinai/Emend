"""Render MasterResume / TailoredResume objects into Jake's-style LaTeX source."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from core.schemas import (
    CustomEntry,
    Education,
    Experience,
    MasterResume,
    Project,
    TailoredResume,
    TailoredSection,
)

from .escaping import escape_latex

_TEMPLATES_DIR = Path(__file__).parent / "templates"

DEFAULT_SECTION_ORDER = ["EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS"]

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


def _ov(overrides: dict[str, str] | None, key: str, default: str) -> str:
    """A user's free-text edit for any non-fact-backed field (name, a
    company name, a degree, ...) -- keyed by a stable path string, separate
    from the fact-grounded `selections` mechanism above. No entry for a
    key: the master/tailored value renders untouched."""
    if overrides and key in overrides:
        return overrides[key]
    return default


def _bullet_row(text: str, source_ids: list[str]) -> dict:
    return {"text": text, "grounded": _grounding_comment(source_ids)}


def _experience_row(
    exp: Experience, bullets: list[dict], overrides: dict[str, str] | None = None
) -> dict:
    # start/end stay separate override keys (matching MasterResume's own
    # fields) rather than one combined "dates" string, so the frontend's
    # live preview -- which only has start/end, not a precomputed display
    # string -- can apply the exact same overrides without a schema mismatch.
    start = _ov(overrides, f"experience:{exp.id}:start", exp.start)
    end = _ov(overrides, f"experience:{exp.id}:end", exp.end)
    return {
        "title": _ov(overrides, f"experience:{exp.id}:title", exp.title),
        "dates": f"{start} -- {end}",
        "company": _ov(overrides, f"experience:{exp.id}:company", exp.company),
        "location": _ov(overrides, f"experience:{exp.id}:location", exp.location),
        "bullets": bullets,
    }


def _project_row(
    proj: Project, bullets: list[dict], overrides: dict[str, str] | None = None
) -> dict:
    return {
        "name": _ov(overrides, f"project:{proj.id}:name", proj.name),
        "tech": _ov(overrides, f"project:{proj.id}:tech", ", ".join(proj.tech)),
        "bullets": bullets,
    }


def _date_range(start: str, end: str) -> str:
    if start and end:
        return f"{start} -- {end}"
    return start or end


def _custom_entry_row(entry: CustomEntry, overrides: dict[str, str] | None = None) -> dict:
    """Custom-section entries are never AI-tailored -- unlike
    `_experience_row`/`_project_row`, this is the only place their facts
    get rendered from, in every mode. `entry.facts` renders as literal
    bullet text directly, each still free-text editable via its own
    `custom:<id>:fact:<fact id>` override, same as any other field here."""
    start = _ov(overrides, f"custom:{entry.id}:start", entry.start)
    end = _ov(overrides, f"custom:{entry.id}:end", entry.end)
    bullets = [
        _bullet_row(_ov(overrides, f"custom:{entry.id}:fact:{f.id}", f.text), [f.id])
        for f in entry.facts
    ]
    return {
        "title": _ov(overrides, f"custom:{entry.id}:title", entry.title),
        "dates": _date_range(start, end),
        "subtitle": _ov(overrides, f"custom:{entry.id}:subtitle", entry.subtitle),
        "location": _ov(overrides, f"custom:{entry.id}:location", entry.location),
        "bullets": bullets,
    }


def _education_row(
    edu: Education, index: int, overrides: dict[str, str] | None = None
) -> dict:
    # coursework_text overridable as one free-text blob (matching how it
    # already displays as one joined line) rather than per-course editing;
    # an override clearing it to "" hides the coursework line entirely.
    coursework_text = _ov(
        overrides, f"education:{index}:coursework", ", ".join(edu.coursework)
    )
    return {
        "school": _ov(overrides, f"education:{index}:school", edu.school),
        "degree": _ov(overrides, f"education:{index}:degree", edu.degree),
        "location": _ov(overrides, f"education:{index}:location", edu.location),
        "grad_date": _ov(overrides, f"education:{index}:grad_date", edu.grad_date),
        "coursework_text": coursework_text,
        "has_coursework": bool(coursework_text),
    }


def _primary_fact_id(bullet) -> str:
    """The key used to select/exclude/reorder a bullet by.

    A bullet always cites at least one fact by construction upstream
    (validate_grounding rejects an empty source_fact_ids before anything
    reaches render) -- but source_fact_ids has no schema-level min length,
    so render must not crash on stored or client-supplied data that
    violates that. A sourceless bullet gets its own object identity
    instead: never equal to a real fact id, so a client's excluded_facts/
    fact_order can't accidentally match it, and unique per bullet within
    this render call, so two sourceless bullets never collide onto the
    same dict key in _reorder_by_key.
    """
    return bullet.source_fact_ids[0] if bullet.source_fact_ids else f"_unsourced_{id(bullet)}"


def _resolve_variant(bullet, selections: dict[str, dict] | None) -> str:
    """Which of a bullet's 3 variants (or a user edit) actually renders.

    Keyed by the bullet's first cited fact -- in practice a bullet almost
    always cites exactly one, and Export's per-line picker treats a bullet
    as one unit regardless. No selection for it: the first variant.
    """
    sel = selections.get(_primary_fact_id(bullet)) if selections else None
    if not sel:
        return bullet.variants[0]
    custom = sel.get("custom_text")
    if custom:
        return custom
    return bullet.variants[sel.get("variant_idx", 0)]


def _exclude_by_key(items: list, excluded: list[str] | None, key) -> list:
    """Drop items whose key is in `excluded` -- the delete side of
    reordering. None/empty excludes everything unchanged."""
    if not excluded:
        return items
    excluded_set = set(excluded)
    return [item for item in items if key(item) not in excluded_set]


def _reorder_by_key(items: list, order: list[str] | None, key) -> list:
    """Reorder `items` to match `order` (a list of `key(item)` values).

    Items whose key isn't in `order` keep their relative position, appended
    after the ordered ones -- a stale order (referencing a fact id that's
    since been deleted) or a partial one (missing a newly added fact) can
    never silently drop a bullet. A key repeated in `order` (a duplicate id
    from a client-side reorder bug or a replayed request) is only honored
    once, at its first occurrence -- otherwise that item renders twice.
    """
    if not order:
        return items
    by_key = {key(item): item for item in items}
    seen: set[str] = set()
    ordered = []
    for k in order:
        if k in by_key and k not in seen:
            ordered.append(by_key[k])
            seen.add(k)
    ordered.extend(item for item in items if key(item) not in seen)
    return ordered


def _tailored_rows(
    sections: list[TailoredSection],
    by_id: dict[str, Experience | Project],
    kind: str,
    selections: dict[str, dict] | None = None,
    fact_order: dict[str, list[str]] | None = None,
    excluded_facts: list[str] | None = None,
    text_overrides: dict[str, str] | None = None,
) -> list:
    rows = []
    for section in sections:
        source = by_id.get(section.ref_id)
        if source is None:
            raise ValueError(
                f"tailored {kind} section references unknown id {section.ref_id!r}"
            )
        remaining_bullets = _exclude_by_key(
            section.bullets, excluded_facts, _primary_fact_id
        )
        ordered_bullets = _reorder_by_key(
            remaining_bullets,
            (fact_order or {}).get(section.ref_id),
            _primary_fact_id,
        )
        bullets = [
            _bullet_row(_resolve_variant(b, selections), b.source_fact_ids)
            for b in ordered_bullets
        ]
        if isinstance(source, Experience):
            rows.append(_experience_row(source, bullets, text_overrides))
        else:
            rows.append(_project_row(source, bullets, text_overrides))
    return rows


def render_tex(
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

    `fact_order` (keyed by an experience/project/custom entry's own id)
    reorders that entry's bullets before rendering -- see `_reorder_by_key`.
    No entry for an id: bullets render in their existing order.
    `experience_order` / `project_order` reorder the entries themselves (by
    their own id in refactor mode, by `ref_id` in tailor mode) the same
    way. `section_order` reorders every top-level section -- the four
    values from DEFAULT_SECTION_ORDER plus one per `master.custom_sections`
    entry (by its own `key`); an omitted or unrecognized entry keeps its
    default relative position. `excluded_facts`/`excluded_experiences`/
    `excluded_projects` drop bullets or whole entries from rendering
    entirely -- the delete side of Export's per-line/per-entry editing.
    Deleting is export-time only: it never touches the confirmed master
    resume or the stored tailored version.

    `text_overrides` (keyed by a stable path string -- "name", "email",
    "phone", "link:<i>", "education:<i>:<field>", "experience:<id>:<field>",
    "project:<id>:<field>", "skills:<category>", "section:<KEY>:heading" for
    any section key including a custom one, "custom:<id>:<field>" and
    "custom:<id>:fact:<fact id>" for a custom entry's own fields/bullets)
    lets a user free-text edit any non-fact-backed field on the resume --
    structural fields, header info, education, skills, even a section's own
    printed heading -- separate from and on top of the fact-grounded
    `selections` mechanism above, which stays scoped to confirmed facts.
    Custom-section entries are never selected via `selections` at all --
    see CustomEntry's own docstring for why they're edit-only.

    Every fact-backed bullet is preceded by a "% grounded: <fact ids>" receipt
    comment — the bullet's source_fact_ids in tailor mode, the fact's own id in
    refactor mode. Coursework and skills carry no receipts: they are confirmed
    master data with no fact ids in the contract, not generated content. A bullet
    with empty source_fact_ids renders an empty receipt; rejecting sourceless
    bullets is the upstream validator's job.
    """
    if tailored is None:
        remaining_experiences = _exclude_by_key(
            master.experiences, excluded_experiences, lambda e: e.id
        )
        remaining_projects = _exclude_by_key(master.projects, excluded_projects, lambda p: p.id)
        experiences = [
            _experience_row(
                e,
                [
                    _bullet_row(f.text, [f.id])
                    for f in _reorder_by_key(
                        _exclude_by_key(e.facts, excluded_facts, lambda f: f.id),
                        (fact_order or {}).get(e.id),
                        lambda f: f.id,
                    )
                ],
                text_overrides,
            )
            for e in _reorder_by_key(remaining_experiences, experience_order, lambda e: e.id)
        ]
        projects = [
            _project_row(
                p,
                [
                    _bullet_row(f.text, [f.id])
                    for f in _reorder_by_key(
                        _exclude_by_key(p.facts, excluded_facts, lambda f: f.id),
                        (fact_order or {}).get(p.id),
                        lambda f: f.id,
                    )
                ],
                text_overrides,
            )
            for p in _reorder_by_key(remaining_projects, project_order, lambda p: p.id)
        ]
        skills = master.skills
    else:
        exp_by_id: dict[str, Experience | Project] = {
            e.id: e for e in master.experiences
        }
        proj_by_id: dict[str, Experience | Project] = {p.id: p for p in master.projects}
        remaining_exp_sections = _exclude_by_key(
            tailored.experiences, excluded_experiences, lambda s: s.ref_id
        )
        remaining_proj_sections = _exclude_by_key(
            tailored.projects, excluded_projects, lambda s: s.ref_id
        )
        experiences = _tailored_rows(
            _reorder_by_key(remaining_exp_sections, experience_order, lambda s: s.ref_id),
            exp_by_id,
            "experience",
            selections,
            fact_order,
            excluded_facts,
            text_overrides,
        )
        projects = _tailored_rows(
            _reorder_by_key(remaining_proj_sections, project_order, lambda s: s.ref_id),
            proj_by_id,
            "project",
            selections,
            fact_order,
            excluded_facts,
            text_overrides,
        )
        skills = tailored.skills

    # A user deleting their phone, email, or a link (clearing its override to
    # "") should make it vanish from the header line entirely -- not leave a
    # broken empty \href{mailto:}{} or a stray "$|$" separator with nothing
    # on one side. Building one ordered, pre-filtered list (instead of fixed
    # phone/email slots plus a separate links loop) lets the template join
    # whatever's actually present with no special-casing for what's missing.
    phone = _ov(text_overrides, "phone", master.phone)
    email = _ov(text_overrides, "email", master.email)
    header_pieces = []
    if phone:
        header_pieces.append({"kind": "text", "text": phone})
    if email:
        header_pieces.append({"kind": "email", "text": email})
    for i, raw_link in enumerate(master.links):
        link = _ov(text_overrides, f"link:{i}", raw_link)
        if not link:
            continue
        header_pieces.append(
            {
                "kind": "link",
                "url": link if link.startswith(("http://", "https://")) else f"https://{link}",
                "text": link.removeprefix("https://").removeprefix("http://"),
            }
        )

    education = [
        _education_row(edu, i, text_overrides) for i, edu in enumerate(master.education)
    ]

    skills_rows = [
        {
            "category": category,
            "items_text": _ov(text_overrides, f"skills:{category}", ", ".join(items)),
        }
        for category, items in skills.items()
    ]

    default_headings = {
        "EDUCATION": "Education",
        "EXPERIENCE": "Experience",
        "PROJECTS": "Projects",
        "SKILLS": "Technical Skills",
    }
    section_headings = {
        key: _ov(text_overrides, f"section:{key}:heading", default)
        for key, default in default_headings.items()
    }

    # Custom sections are per-resume (not a fixed module constant like
    # DEFAULT_SECTION_ORDER), and always render straight from confirmed
    # master data -- never from `tailored`, in either mode, per the
    # edit/format-only design (see CustomEntry's own docstring).
    custom_by_key = {
        cs.key: {
            "heading": _ov(text_overrides, f"section:{cs.key}:heading", cs.heading),
            "entries": [_custom_entry_row(entry, text_overrides) for entry in cs.entries],
        }
        for cs in master.custom_sections
    }

    context = {
        "name": _ov(text_overrides, "name", master.name),
        "header_pieces": header_pieces,
        "education": education,
        "experiences": experiences,
        "projects": projects,
        "skills": skills_rows,
        "section_headings": section_headings,
        "custom_by_key": custom_by_key,
        "section_order": _reorder_by_key(
            DEFAULT_SECTION_ORDER + list(custom_by_key), section_order, lambda s: s
        ),
    }
    return _env.get_template("resume.tex.jinja").render(**context)
