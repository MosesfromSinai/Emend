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


def test_empty_tailored_skills_falls_back_to_master(master, tailored):
    tailored.skills = {}
    tex = render_tex(master, tailored)
    assert r"\textbf{Languages}{: Ada, Assembly, Python}" in tex


def test_injection_in_every_field_is_escaped(master):
    master.name = r"Evil \write18{rm -rf /} & Co"
    master.experiences[0].company = "100% $legit_corp^{tm}"
    tex = render_tex(master, None)
    assert r"\write18" not in tex.replace(r"\textbackslash{}write18", "")
    assert r"\textbackslash{}write18\{rm -rf /\}" in tex
    assert r"100\% \$legit\_corp\textasciicircum{}\{tm\}" in tex
