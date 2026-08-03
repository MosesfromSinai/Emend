from core.normalize import unwrap_text


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
