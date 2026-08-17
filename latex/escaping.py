"""Injection-safe escaping for every string rendered into LaTeX."""

import re
from typing import Any

_ESCAPES: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

# Single-pass substitution so replacement text is never itself re-escaped.
_PATTERN = re.compile(r"[\\&%$#_{}~^]")

# XeTeX/Tectonic is Unicode-native, so these render as directed rather than
# being inert: bidi overrides (U+202A-U+202E LRE/RLE/PDF/LRO/RLO, U+2066-
# U+2069 LRI/RLI/FSI/PDI, U+061C ALM, U+200E/F LRM/RLM) can make digits/
# words display reordered from how the stored string reads, and zero-width
# characters (U+200B/C/D ZWSP/ZWNJ/ZWJ, U+2060 word joiner, U+FEFF BOM) can
# hide invisible content in the PDF's extracted text -- a real integrity
# gap for a pipeline whose whole model is "what you confirmed is what
# renders." None of these are meaningful in resume content, so they're
# stripped rather than escaped/displayed. Spelled as explicit \u escapes,
# not literal characters, so the pattern stays reviewable in a diff.
_INVISIBLE_UNICODE_PATTERN = re.compile(
    "[\u061c\u200b\u200c\u200d\u200e\u200f\u2060"
    "\u202a\u202b\u202c\u202d\u202e"
    "\u2066\u2067\u2068\u2069\ufeff]"
)


class RawLatex(str):
    """A value already prepared for LaTeX output -- passed through as-is by
    escape_latex (used as the Jinja environment's `finalize`) instead of
    being escaped a second time. Used for the target argument of \\href,
    which needs escape_latex_url's narrower escaping, not this module's
    prose escaping -- see escape_latex_url's docstring for why."""


def escape_latex(value: Any) -> str:
    if isinstance(value, RawLatex):
        return value
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    # A blank line (two+ newlines) becomes a literal LaTeX \par when this
    # text lands inside a \textbf/tabular* argument (e.g. resumeSubheading's
    # title/dates/company/location) -- "Paragraph ended before \textbf was
    # complete," a real compile break from an ordinary pasted resume, not
    # an adversarial one. No field here is meant to carry multi-line
    # structure, so any run of newlines collapses to a single space.
    text = re.sub(r"\s*\n\s*", " ", text)
    text = _INVISIBLE_UNICODE_PATTERN.sub("", text)
    return _PATTERN.sub(lambda m: _ESCAPES[m.group()], text)


# hyperref changes catcodes for # $ % & ~ _ ^ specifically within \href's own
# argument, so those need to stay literal there for the link to actually
# work -- escaping them the way prose does (e.g. "_" -> "\_") bakes a
# backslash into the URL/mailto target itself and breaks the link, exactly
# the bug this exists to avoid. Only backslash and braces can still break
# out of \href{...}'s argument grouping or inject a control sequence, so
# only those two are escaped here.
_URL_ESCAPES: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
}
_URL_PATTERN = re.compile(r"[\\{}]")


def escape_latex_url(value: Any) -> RawLatex:
    if value is None:
        return RawLatex("")
    text = value if isinstance(value, str) else str(value)
    return RawLatex(_URL_PATTERN.sub(lambda m: _URL_ESCAPES[m.group()], text))
