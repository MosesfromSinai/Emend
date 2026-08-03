"""Pre-LLM text cleanup: undo PDF/editor line-wrapping before structuring.

Resumes copy-pasted from a PDF viewer often hard-wrap every visual line with
a real newline, which breaks sentence-level fact splitting downstream.
`unwrap_text` heuristically tells a genuine line break (a new bullet, a new
paragraph) apart from a soft wrap (the renderer just ran out of width) and
rejoins the latter, before either the mock parser or the LLM ever sees the
text. Pure Python, no LLM calls, no network.
"""

import re
import unicodedata

BULLET_START_PATTERN = re.compile(r"^[•●○◦‣▪∙·\-*]\s*|^\d+[.)]\s")
TERMINAL_PUNCT = (".", "!", "?", ":")
HYPHENATION_PATTERN = re.compile(r"(?<=[a-z])-$")

_UNICODE_BULLETS = "●○◦‣▪∙"
_QUOTE_MAP = {"“": '"', "”": '"', "‘": "'", "’": "'"}
_DASH_MAP = {"–": "-", "—": "-"}


def _normalize_chars(text: str) -> str:
    text = text.replace("\xa0", " ")
    for glyph in _UNICODE_BULLETS:
        text = text.replace(glyph, "•")
    for smart, plain in _QUOTE_MAP.items():
        text = text.replace(smart, plain)
    for dash, plain in _DASH_MAP.items():
        text = text.replace(dash, plain)
    return unicodedata.normalize("NFKC", text)


def _join_block_lines(lines: list[str]) -> str:
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if out and HYPHENATION_PATTERN.search(out[-1]):
            out[-1] = out[-1][:-1] + stripped
            continue
        if (
            out
            and not out[-1].endswith(TERMINAL_PUNCT)
            and not BULLET_START_PATTERN.match(stripped)
        ):
            out[-1] = f"{out[-1]} {stripped}"
            continue
        out.append(stripped)
    return "\n".join(out)


def unwrap_text(raw: str) -> str:
    """Rejoin soft-wrapped lines while preserving bullets and paragraph breaks."""
    text = _normalize_chars(raw)
    blocks = [b for b in re.split(r"\n\s*\n+", text.strip()) if b.strip()]
    joined = [_join_block_lines(block.splitlines()) for block in blocks]
    result = "\n\n".join(b for b in joined if b)
    return re.sub(r"[ \t]+", " ", result)
