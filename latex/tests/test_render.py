import pytest

from latex.render import render_tex


def test_refactor_mode_renders_master_facts(master):
    tex = render_tex(master, None)
    assert r"\textbf{\Huge \scshape Ada Lovelace}" in tex
    assert "Software Engineer Intern" in tex
    assert "Jun 2023 -- Aug 2023" in tex
    # facts become bullets
    assert r"\resumeItem{Wrote the first published algorithm" in tex
    # escaping applied to user content
    assert r"Babbage \& Co" in tex
    assert r"40\%" in tex
    assert r"analytical\_engine" in tex
    assert r"\textasciitilde{}25\%" in tex
    # skills from master
    assert r"\textbf{Languages}{: Ada, Assembly, Python}" in tex


def test_tailor_mode_swaps_bullets_keeps_structure(master, tailored):
    tex = render_tex(master, tailored)
    # structural fields still come from master
    assert r"Babbage \& Co" in tex
    assert "Software Engineer Intern" in tex
    assert "Jun 2023 -- Aug 2023" in tex
    # tailored bullets replace master facts
    assert "Authored the first machine-executable algorithm" in tex
    assert "Wrote the first published algorithm" not in tex
    # sections not in the tailored selection are dropped
    assert "Royal Society" not in tex
    # tailored skills win
    assert r"\textbf{Languages}{: Python, Ada}" in tex
    assert "Assembly" not in tex


def test_tailor_mode_unknown_ref_id_raises(master, tailored):
    tailored.experiences[0].ref_id = "nonexistent"
    with pytest.raises(ValueError, match="unknown id 'nonexistent'"):
        render_tex(master, tailored)


def test_education_rendered(master):
    tex = render_tex(master, None)
    assert "University of London" in tex
    assert "B.S. in Mathematics" in tex
    assert r"\textbf{Relevant Coursework}{: Analytical Engines, Number Theory" in tex


def test_links_get_scheme_and_display(master):
    tex = render_tex(master, None)
    assert r"\href{https://linkedin.com/in/ada-lovelace}" in tex
    assert r"\href{mailto:ada@example.com}" in tex


def test_empty_sections_are_omitted(master):
    master.projects = []
    master.skills = {}
    tex = render_tex(master, None)
    assert r"\section{Projects}" not in tex
    assert r"\section{Technical Skills}" not in tex
    assert r"\section{Experience}" in tex


def test_empty_tailored_skills_omits_section_not_master_fallback(master, tailored):
    # An empty tailored.skills is a deliberate "nothing relevant" decision
    # (core/prompts.py instructs filtering out categories with no overlap),
    # not a missing value -- it must never fall back to master's skills.
    tailored.skills = {}
    tex = render_tex(master, tailored)
    assert r"\section{Technical Skills}" not in tex
    assert "Ada, Assembly, Python" not in tex


def test_refactor_bullets_carry_own_fact_id_receipts(master):
    tex = render_tex(master, None)
    lines = [line.strip() for line in tex.splitlines()]
    for section in (*master.experiences, *master.projects):
        for fact in section.facts:
            idx = lines.index(f"% grounded: {fact.id}")
            assert lines[idx + 1].startswith(r"\resumeItem{")
    idx = lines.index("% grounded: BAB-01")
    assert lines[idx + 1].startswith(r"\resumeItem{Wrote the first published algorithm")


def test_tailor_bullets_carry_source_fact_ids(master, tailored):
    tex = render_tex(master, tailored)
    lines = [line.strip() for line in tex.splitlines()]
    idx = lines.index("% grounded: BAB-01")
    assert lines[idx + 1].startswith(
        r"\resumeItem{Authored the first machine-executable"
    )
    # merged bullets list every contributing fact
    idx = lines.index("% grounded: BERN-01, BERN-02")
    assert lines[idx + 1].startswith(r"\resumeItem{Built a mechanical Bernoulli")


def test_every_fact_backed_bullet_has_exactly_one_receipt(master, tailored):
    # coursework/skills are confirmed master data, not generated content — no receipts
    refactor = render_tex(master, None)
    n_facts = sum(len(s.facts) for s in (*master.experiences, *master.projects))
    assert refactor.count("% grounded:") == n_facts
    tailor = render_tex(master, tailored)
    n_bullets = sum(len(s.bullets) for s in (*tailored.experiences, *tailored.projects))
    assert tailor.count("% grounded:") == n_bullets


def test_empty_source_fact_ids_still_renders_receipt(master, tailored):
    # sourceless bullets are the upstream validator's problem; the receipt stays truthful
    tailored.experiences[0].bullets[0].source_fact_ids = []
    tex = render_tex(master, tailored)
    assert "% grounded:" in [line.strip() for line in tex.splitlines()]


def test_injection_in_every_field_is_escaped(master):
    master.name = r"Evil \write18{rm -rf /} & Co"
    master.experiences[0].company = "100% $legit_corp^{tm}"
    tex = render_tex(master, None)
    assert r"\write18" not in tex.replace(r"\textbackslash{}write18", "")
    assert r"\textbackslash{}write18\{rm -rf /\}" in tex
    assert r"100\% \$legit\_corp\textasciicircum{}\{tm\}" in tex
