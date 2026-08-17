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
