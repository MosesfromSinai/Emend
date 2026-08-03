from core.normalize import reattach_orphan_dates, split_inline_bullets, unwrap_text


def test_joins_hard_mid_sentence_wrap():
    raw = (
        "Developed 25+ integration tests using behave and Gherkin on the\n"
        "Advanced C2 Systems team, validating end-to-end message flow."
    )
    assert unwrap_text(raw) == (
        "Developed 25+ integration tests using behave and Gherkin on the "
        "Advanced C2 Systems team, validating end-to-end message flow."
    )


def test_does_not_join_across_a_new_bullet():
    raw = "- Wrote the first algorithm.\n- Improved throughput by 40%."
    assert unwrap_text(raw) == "- Wrote the first algorithm.\n- Improved throughput by 40%."


def test_does_not_join_after_terminal_punctuation_or_colon():
    raw = "Skills:\nPython, Docker, SQL."
    assert unwrap_text(raw) == "Skills:\nPython, Docker, SQL."


def test_rejoins_hyphenated_line_wrap():
    raw = "Automated startup and shut-\ndown scripts for RHEL 8 VMs."
    assert unwrap_text(raw) == "Automated startup and shutdown scripts for RHEL 8 VMs."


def test_preserves_blank_line_block_breaks():
    raw = "Experience heading\n\nProject heading"
    assert unwrap_text(raw) == "Experience heading\n\nProject heading"


def test_normalizes_unicode_bullets_quotes_dashes_and_nbsp():
    raw = "▪ Shipped the “fast path” feature–a big win."
    assert unwrap_text(raw) == '• Shipped the "fast path" feature-a big win.'


def test_collapses_whitespace_runs():
    raw = "Sam   Sample\t\tRow"
    assert unwrap_text(raw) == "Sam Sample Row"


def test_reattaches_orphan_bare_year_to_preceding_header():
    raw = "ACM @ UCR Riverside, CA\n2025\nDeveloped the club site."
    assert reattach_orphan_dates(raw) == (
        "ACM @ UCR Riverside, CA 2025\nDeveloped the club site."
    )


def test_reattaches_orphan_date_range_to_preceding_header():
    raw = "Software Engineer Intern\nJun 2025 - Aug 2025\nWrote tests."
    assert reattach_orphan_dates(raw) == (
        "Software Engineer Intern Jun 2025 - Aug 2025\nWrote tests."
    )


def test_does_not_reattach_onto_a_header_that_already_has_a_date():
    raw = "Software Engineer Intern Jun 2025 - Aug 2025\n2026\nWrote tests."
    # skips the already-dated header and keeps searching further back
    assert "Intern Jun 2025 - Aug 2025 2026" not in reattach_orphan_dates(raw)


def test_reattach_skips_a_bullet_fact_line_to_find_the_real_header():
    raw = "TermIt | C++, CMake, GoogleTest\n• Developed a CLI task manager.\n2025"
    assert reattach_orphan_dates(raw) == (
        "TermIt | C++, CMake, GoogleTest 2025\n• Developed a CLI task manager."
    )


def test_split_inline_bullets_breaks_header_from_first_bullet():
    raw = "TermIt | C++, CMake, GoogleTest • Developed a CLI task manager."
    assert split_inline_bullets(raw) == (
        "TermIt | C++, CMake, GoogleTest\n• Developed a CLI task manager."
    )


def test_split_inline_bullets_preserves_a_leading_bullet():
    raw = "• Wrote 20 tests • Fixed 5 bugs"
    assert split_inline_bullets(raw) == "• Wrote 20 tests\n• Fixed 5 bugs"


def test_split_inline_bullets_leaves_bulletless_lines_alone():
    raw = "Just a plain sentence."
    assert split_inline_bullets(raw) == raw
