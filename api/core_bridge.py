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

from core.schemas import JDExtract, MasterResume, Report, TailoredResume


class CoreUnavailableError(RuntimeError):
    """core's pipeline functions have not landed yet (pre-MOCK=1 merge)."""


def _core_fn(name: str):
    import core

    fn = getattr(core, name, None)
    if fn is None:
        raise CoreUnavailableError(
            f"core.{name} is not available yet — waiting on Workflow A's MOCK=1 pipeline"
        )
    return fn


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
    master: MasterResume, tailored: TailoredResume | None
) -> tuple[str, str, str]:
    """(tex, pdf_path, log); pdf_path == "" means compile failure, log says why."""
    import latex

    return latex.render_and_compile(master, tailored)
