"""The single seam between api and the core/latex workflows.

All pipeline calls go through here so that when Workflow A lands (or adjusts a
signature), only this file changes. Imports are lazy: the app must boot in
compose today, before `core`'s pipeline functions exist — callers get a
`CoreUnavailableError` they can map to a clean 503/failed status.

Expected `core` surface (per 00-project-brief.md + 01-teammate-Moses.md):
    structure_resume(text) -> MasterResume
    parse_jd(text) -> JDExtract
    keyword_match(jd, master) -> (score: float, matched: list[str], missing: list[str])
    tailor(master, jd) -> TailoredResume
    validate(master, tailored) -> (grounding_ok: bool, verdicts: list[BulletVerdict])

Seam proposal flagged to Moses: the brief doesn't pin `validate`'s signature.
We assume it returns (grounding_ok, verdicts) and the api assembles `Report`
by combining that with `keyword_match`'s output (match scoring is
deterministic and not validation's business). If core prefers returning a
full `Report`, only `validate` below changes.
"""

import httpx

from core.schemas import JDExtract, MasterResume, Report, TailoredResume

JD_FETCH_TIMEOUT_SECONDS = 10

# Without a browser-like User-Agent, httpx's default ("python-httpx/...")
# gets silently dropped by bot-protection CDNs in front of major ATS/careers
# sites (confirmed against a real Roblox/Akamai-fronted posting: no UA hangs
# until the client times out, a normal browser UA returns instantly). This
# doesn't claim to *be* a browser beyond the one header those systems key
# on -- it's still a plain HTML fetch, no JS execution.
JD_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class CoreUnavailableError(RuntimeError):
    """core's pipeline functions have not landed yet (pre-MOCK=1 merge)."""


def fetch_jd_text(url: str) -> str:
    """Fetch a job-posting URL server-side and extract its JD text.

    Shared by the async tailor job and /jd/preview's live score card, so a
    fetch/extract fix lands in exactly one place.
    """
    response = httpx.get(
        url,
        timeout=JD_FETCH_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers=JD_FETCH_HEADERS,
    )
    response.raise_for_status()
    return html_to_jd_text(response.text)


def _core_fn(name: str):
    import core

    fn = getattr(core, name, None)
    if fn is None:
        raise CoreUnavailableError(
            f"core.{name} is not available yet — waiting on Workflow A's MOCK=1 pipeline"
        )
    return fn


def pdf_to_text(data: bytes) -> str:
    """PdfExtractionError (a ValueError subclass) maps to 422 same as any
    other bad structure_resume input -- callers don't need a special case."""
    from core.extract import pdf_to_text as _pdf_to_text

    return _pdf_to_text(data)


def html_to_jd_text(html: str) -> str:
    from core.jd_text import html_to_jd_text as _html_to_jd_text

    return _html_to_jd_text(html)


def structure_resume(text: str) -> MasterResume:
    return _core_fn("structure_resume")(text)


def parse_jd(text: str) -> JDExtract:
    return _core_fn("parse_jd")(text)


def keyword_match(
    jd: JDExtract, master: MasterResume
) -> tuple[float, list[str], list[str]]:
    return _core_fn("keyword_match")(jd, master)


def tailor(master: MasterResume, jd: JDExtract) -> TailoredResume:
    return _core_fn("tailor")(master, jd)


def refactor(master: MasterResume) -> TailoredResume:
    """No-JD path: wraps confirmed facts as a TailoredResume (3 identical
    variants each) so Export's per-line edit controls work the same way
    here as they do for a tailored resume -- refactor mode isn't just a
    typeset pass-through, it's still a resume someone may want to tweak."""
    return _core_fn("refactor")(master)


def validate(
    master: MasterResume,
    tailored: TailoredResume,
    match_score: float,
    matched_keywords: list[str],
    missing_keywords: list[str],
) -> Report:
    grounding_ok, verdicts = _core_fn("validate")(master, tailored)
    return Report(
        match_score=match_score,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        grounding_ok=grounding_ok,
        verdicts=verdicts,
    )


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
    """(tex, pdf_path, log); pdf_path == "" means compile failure, log says why."""
    import latex

    return latex.render_and_compile(
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
) -> str:
    """Cheap tex-only render (no compile) -- used for the live Export preview."""
    import latex.render

    return latex.render.render_tex(
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
    )
