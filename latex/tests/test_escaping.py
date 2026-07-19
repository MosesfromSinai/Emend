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


def test_non_strings():
    assert escape_latex(None) == ""
    assert escape_latex(42) == "42"
    assert escape_latex("") == ""
