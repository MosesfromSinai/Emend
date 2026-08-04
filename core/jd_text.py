"""HTML -> plain job-description text, for the job-URL ingestion path.

Pure Python (selectolax), offline, no network. The caller (api, in a later
task) fetches the posting URL and hands this module the raw HTML; core never
makes a network call itself.
"""

import json
import re
from html import unescape

from selectolax.parser import HTMLParser

STRIP_TAGS = ("script", "style", "nav", "header", "footer", "aside", "a", "button")
MAIN_SELECTORS = ("main", "article", "[role=main]")
MAX_JD_CHARS = 20_000

_TAG_RE = re.compile(r"<[^>]+>")

# A "Related Jobs" / "Similar Openings" carousel is real content of the page
# but not of the posting -- on custom-templated careers sites it commonly
# sits as a sibling <section> inside <main> (confirmed against a real
# Roblox posting), so STRIP_TAGS' semantic-tag list alone doesn't catch it.
# Matched by heading text and removed by walking up to the nearest <section>
# ancestor, never past it -- this must never reach up to <main>/<body>.
_CHROME_HEADINGS = re.compile(
    r"^(?:related|similar|other|more)\s+(?:jobs?|openings?|positions?|roles?|opportunities)|"
    r"^jobs?\s+you\s+might\s+like|^share\s+this\s+job|"
    r"^explore\s+(?:more|other)\s+(?:jobs?|roles?|opportunities)|"
    r"^recently\s+viewed",
    re.IGNORECASE,
)


def _strip_chrome_sections(tree: HTMLParser) -> None:
    for heading in tree.css("h1, h2, h3, h4, h5, h6"):
        text = heading.text(strip=True)
        if not text or not _CHROME_HEADINGS.search(text):
            continue
        node = heading.parent
        while node is not None and node.tag not in ("section", "article", "body", "html"):
            node = node.parent
        if node is not None and node.tag in ("section", "article"):
            node.decompose()


def _strip_tags(fragment: str) -> str:
    """Plain text from an HTML fragment (e.g. a JSON-LD `description`, which
    is itself HTML, not the page markup this module otherwise parses)."""
    return " ".join(unescape(_TAG_RE.sub(" ", fragment)).split())


def _job_posting_from_json_ld(tree: HTMLParser) -> str | None:
    """Many ATS platforms render the job page client-side (React/etc.) but
    still embed the full posting as schema.org JobPosting JSON-LD for SEO --
    read straight from that when the visible DOM is just a JS-only shell.
    Must run before STRIP_TAGS below removes every <script> on the page."""
    for node in tree.css('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.text())
        except (ValueError, TypeError):
            continue
        for candidate in data if isinstance(data, list) else [data]:
            if not isinstance(candidate, dict) or candidate.get("@type") != "JobPosting":
                continue
            description = candidate.get("description")
            if isinstance(description, str) and description.strip():
                return _strip_tags(description)
    return None


def html_to_jd_text(html: str) -> str:
    """Extract the densest readable block of a job-posting page as plain text."""
    tree = HTMLParser(html)
    json_ld_text = _job_posting_from_json_ld(tree)
    _strip_chrome_sections(tree)

    for tag in STRIP_TAGS:
        for node in tree.css(tag):
            node.decompose()

    candidates = [node for selector in MAIN_SELECTORS for node in tree.css(selector)]
    if candidates:
        best = max(candidates, key=lambda node: len(node.text(strip=True)))
    else:
        best = tree.body

    dom_text = best.text(separator=" ", strip=True) if best is not None else ""
    dom_text = " ".join(dom_text.split())

    # A JS-rendered SPA shell's visible DOM is typically just a loading
    # message ("enable JavaScript...") -- prefer the JSON-LD posting (a
    # structured, purpose-built signal) unless the DOM text is clearly the
    # richer of the two, which only happens on genuinely server-rendered
    # pages that also happen to carry a (then-redundant) JobPosting block.
    text = json_ld_text if json_ld_text and len(json_ld_text) >= len(dom_text) else dom_text
    return text[:MAX_JD_CHARS]
