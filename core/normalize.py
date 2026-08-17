"""Pre-LLM text cleanup: undo PDF/editor line-wrapping before structuring.

Resumes copy-pasted from a PDF viewer often hard-wrap every visual line with
a real newline, which breaks sentence-level fact splitting downstream.
`unwrap_text` heuristically tells a genuine line break (a new bullet, a new
paragraph) apart from a soft wrap (the renderer just ran out of width) and
rejoins the latter, before either the mock parser or the LLM ever sees the
text. Pure Python, no LLM calls, no network.
"""

import logging
import re
import unicodedata

logger = logging.getLogger("emend.core.normalize")

BULLET_START_PATTERN = re.compile(r"^[•●○◦‣▪∙·\-*]\s*|^\d+[.)]\s")
TERMINAL_PUNCT = (".", "!", "?", ":")
HYPHENATION_PATTERN = re.compile(r"(?<=[a-z])-$")

_YEAR = r"(?:19|20)\d{2}"
BARE_YEAR_LINE_PATTERN = re.compile(rf"^{_YEAR}$")
BARE_DATE_RANGE_LINE_PATTERN = re.compile(
    rf"^(?:[A-Za-z]{{3,9}}\.?\s*{_YEAR}|\d{{1,2}}/{_YEAR}|{_YEAR})\s*-\s*"
    rf"(?:[A-Za-z]{{3,9}}\.?\s*{_YEAR}|\d{{1,2}}/{_YEAR}|{_YEAR}|Present|Current)$",
    re.IGNORECASE,
)
_LINE_HAS_DATE_PATTERN = re.compile(
    rf"(?:[A-Za-z]{{3,9}}\.?\s*{_YEAR}|\d{{1,2}}/{_YEAR}|{_YEAR})\s*-\s*"
    rf"(?:[A-Za-z]{{3,9}}\.?\s*{_YEAR}|\d{{1,2}}/{_YEAR}|{_YEAR}|Present|Current)",
    re.IGNORECASE,
)
INLINE_BULLET_PATTERN = re.compile(r"(?<=\S)\s*[•●○◦‣▪∙]\s*")

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


def reattach_orphan_dates(text: str) -> str:
    """Merge a bare year/date-range line into the nearest dateless header above it.

    PDF text extraction often emits a right-aligned date on its own line,
    disconnected from the title/company line it belongs with. Reattaching it
    before segmentation means date-range detection can find it where it's
    expected: on the header line itself.
    """
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        is_orphan_date = bool(
            BARE_YEAR_LINE_PATTERN.match(stripped)
            or BARE_DATE_RANGE_LINE_PATTERN.match(stripped)
        )
        if not is_orphan_date:
            out.append(line)
            continue
        for i in range(len(out) - 1, -1, -1):
            candidate = out[i].strip()
            if not candidate:
                continue
            if (
                _LINE_HAS_DATE_PATTERN.search(candidate)
                or BARE_YEAR_LINE_PATTERN.match(candidate)
                or BULLET_START_PATTERN.match(candidate)
                or candidate.endswith((".", "!", "?"))
            ):
                # already-dated, or a fact/bullet line -- not a header, keep
                # searching further back for the real one
                continue
            out[i] = f"{out[i]} {stripped}"
            # Never the actual text: `stripped`/`candidate` are fragments of
            # the user's real resume (a date, a company/school header line),
            # and INFO-level logs commonly flow into a log aggregator with
            # no PII-retention policy of its own. Lengths are enough to
            # confirm the heuristic fired and tune how often it does.
            logger.debug(
                "reattached an orphan date (%d chars) to a header line (%d chars)",
                len(stripped),
                len(candidate),
            )
            break
        else:
            out.append(line)
    return "\n".join(out)


def split_inline_bullets(text: str) -> str:
    """Break a bullet glyph out onto its own line wherever it appears.

    PDF extraction sometimes runs a header straight into its first bullet
    with no newline between them ("TermIt | C++, CMake • Developed..."),
    which then reads as one line neither a clean header nor a clean fact.
    """
    out: list[str] = []
    for line in text.splitlines():
        leading = BULLET_START_PATTERN.match(line)
        prefix, rest = (line[: leading.end()], line[leading.end() :]) if leading else ("", line)
        parts = INLINE_BULLET_PATTERN.split(rest)
        if len(parts) == 1:
            out.append(line)
            continue
        out.append(prefix + parts[0])
        out.extend(f"• {part}" for part in parts[1:] if part.strip())
    return "\n".join(out)
