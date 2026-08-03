"""HTML -> plain job-description text, for the job-URL ingestion path.

Pure Python (selectolax), offline, no network. The caller (api, in a later
task) fetches the posting URL and hands this module the raw HTML; core never
makes a network call itself.
"""

from selectolax.parser import HTMLParser

STRIP_TAGS = ("script", "style", "nav", "header", "footer", "aside")
MAIN_SELECTORS = ("main", "article", "[role=main]")
MAX_JD_CHARS = 20_000


def html_to_jd_text(html: str) -> str:
    """Extract the densest readable block of a job-posting page as plain text."""
    tree = HTMLParser(html)
    for tag in STRIP_TAGS:
        for node in tree.css(tag):
            node.decompose()

    candidates = [node for selector in MAIN_SELECTORS for node in tree.css(selector)]
    if candidates:
        best = max(candidates, key=lambda node: len(node.text(strip=True)))
    else:
        best = tree.body

    text = best.text(separator=" ", strip=True) if best is not None else ""
    text = " ".join(text.split())
    return text[:MAX_JD_CHARS]
