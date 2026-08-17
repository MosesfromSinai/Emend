from latex.escaping import escape_latex


def test_each_special_character():
    assert escape_latex("&") == r"\&"
    assert escape_latex("%") == r"\%"
    assert escape_latex("$") == r"\$"
    assert escape_latex("#") == r"\#"
    assert escape_latex("_") == r"\_"
    assert escape_latex("{") == r"\{"
    assert escape_latex("}") == r"\}"
    assert escape_latex("~") == r"\textasciitilde{}"
    assert escape_latex("^") == r"\textasciicircum{}"
    assert escape_latex("\\") == r"\textbackslash{}"


def test_combined_string():
    assert (
        escape_latex(r"a&b%c$d#e_f{g}h~i^j\k")
        == r"a\&b\%c\$d\#e\_f\{g\}h\textasciitilde{}i\textasciicircum{}j\textbackslash{}k"
    )


def test_backslash_not_double_escaped():
    # \{ must become escaped-backslash + escaped-brace, with the inserted
    # braces of \textbackslash{} left untouched
    assert escape_latex(r"\{") == r"\textbackslash{}\{"


def test_plain_string_untouched():
    assert escape_latex("Software Engineer, 2024") == "Software Engineer, 2024"


def test_blank_line_collapses_to_a_space():
    # A blank line inside a \tabular*/\textbf argument (e.g. a
    # resumeSubheading title/dates/company/location) becomes a literal
    # LaTeX \par and breaks compilation -- plausible from pasting a
    # Word/PDF resume, not even adversarial.
    assert escape_latex("Eng\n\nBAD") == "Eng BAD"


def test_single_newline_collapses_to_a_space():
    assert escape_latex("Eng\nBAD") == "Eng BAD"


def test_strips_bidi_and_zero_width_unicode():
    # XeTeX/Tectonic is Unicode-native and renders these as directed rather
    # than treating them as inert -- a right-to-left override can make
    # digits/words display reordered from how the stored string reads, and
    # zero-width characters can hide invisible content in the extracted
    # text, a real integrity gap for a "what you confirmed is what
    # renders" pipeline. Spelled as explicit \u escapes so the invisible
    # characters under test stay visible in a diff.
    assert escape_latex("A\u202eB") == "AB"  # RIGHT-TO-LEFT OVERRIDE
    assert escape_latex("A\u200bB") == "AB"  # ZERO WIDTH SPACE
    assert escape_latex("A\ufeffB") == "AB"  # BOM / ZERO WIDTH NO-BREAK SPACE


def test_non_strings():
    assert escape_latex(None) == ""
    assert escape_latex(42) == "42"
    assert escape_latex("") == ""
