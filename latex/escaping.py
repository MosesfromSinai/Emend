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


def escape_latex(value: Any) -> str:
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    return _PATTERN.sub(lambda m: _ESCAPES[m.group()], text)
