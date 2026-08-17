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

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx

from core.schemas import JDExtract, MasterResume, Report, TailoredResume

JD_FETCH_TIMEOUT_SECONDS = 10
JD_FETCH_MAX_REDIRECTS = 5
# SSRF-safe (_assert_public_http_url) doesn't bound response size -- Emend
# runs as a single API instance (see api/rate_limit.py), so one huge or
# slow-drip job-posting response fully buffered into memory can OOM the
# whole process for every user, not just the requester. Mirrors
# core.extract.MAX_PDF_BYTES: a single fetched document, capped the same
# regardless of source.
JD_FETCH_MAX_BYTES = 5 * 1024 * 1024


class JdUrlBlockedError(ValueError):
    """A user-supplied JD URL resolves somewhere this server should never
    fetch from on someone else's behalf -- loopback, a private/internal
    range, or a cloud metadata endpoint. Raised before any request is made
    for the initial URL, and again on every redirect hop, since a public
    URL can redirect straight into an internal address otherwise."""


def _assert_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise JdUrlBlockedError(f"unsupported URL scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise JdUrlBlockedError("URL has no host")
    try:
        addrinfo = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise JdUrlBlockedError(f"could not resolve host: {parsed.hostname}") from exc
    # Every address a hostname resolves to is checked, not just the first --
    # a name can round-robin across both a public and an internal address.
    # Note: this resolves the host once here and httpx resolves it again
    # when it actually connects a moment later, so a DNS answer that
    # changes in between (DNS rebinding) isn't caught by this check alone;
    # accepted here as a real but low-probability residual risk for this
    # app's threat model, not something worth a custom transport for.
    for _family, _type, _proto, _canon, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        # not is_global (rather than enumerating is_private/is_loopback/etc)
        # so this doesn't miss a range the enumerated list forgot -- it
        # already had: is_private/is_loopback/is_link_local/is_multicast/
        # is_reserved/is_unspecified were all True for every RFC1918 range,
        # but every one of them is False for 100.64.0.0/10 (RFC 6598,
        # carrier-grade NAT -- real internal cloud/k8s networks use it),
        # which is_global correctly still rejects.
        if not ip.is_global:
            raise JdUrlBlockedError(f"URL resolves to a non-public address: {ip}")

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

    Redirects are followed manually, one hop at a time, with every hop
    re-validated -- an SSRF-safe URL can still redirect straight into
    localhost/an internal address/a cloud metadata endpoint, so trusting
    httpx's own `follow_redirects` would only ever check the URL the user
    supplied, not where it actually ends up.
    """
    current = url
    for _ in range(JD_FETCH_MAX_REDIRECTS + 1):
        _assert_public_http_url(current)
        # Streamed, not httpx.get(), so an oversized response can be
        # aborted mid-download instead of already sitting fully in memory
        # by the time its size is checked.
        with httpx.stream(
            "GET",
            current,
            timeout=JD_FETCH_TIMEOUT_SECONDS,
            follow_redirects=False,
            headers=JD_FETCH_HEADERS,
        ) as response:
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    break
                current = urljoin(current, location)
                continue
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_bytes():
                body += chunk
                if len(body) > JD_FETCH_MAX_BYTES:
                    raise JdUrlBlockedError(
                        f"job posting response exceeds {JD_FETCH_MAX_BYTES} bytes"
                    )
            html = body.decode(response.encoding or "utf-8", errors="replace")
            return html_to_jd_text(html)
    raise JdUrlBlockedError(f"too many redirects fetching {url}")


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


def polish(master: MasterResume) -> TailoredResume:
    """No-JD path, opted into: an LLM rewrite for stronger wording without a
    posting to target, still grounded/judged like a real tailor."""
    return _core_fn("polish")(master)


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
    text_overrides: dict[str, str] | None = None,
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
        text_overrides=text_overrides,
    )
