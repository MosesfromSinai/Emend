import pytest

from core.schemas import TailoredBullet, TailoredSection
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


def test_fact_order_reorders_tailored_bullets(master, tailored):
    tex = render_tex(master, tailored, fact_order={"BAB": ["BAB-02", "BAB-01"]})
    idx_02 = tex.index("Boosted processing throughput")
    idx_01 = tex.index("Authored the first machine-executable")
    assert idx_02 < idx_01


def test_fact_order_reorders_refactor_bullets(master):
    exp_id = master.experiences[0].id
    fact_ids = [f.id for f in master.experiences[0].facts]
    tex = render_tex(master, None, fact_order={exp_id: list(reversed(fact_ids))})
    idx_first = tex.index(f"% grounded: {fact_ids[0]}")
    idx_last = tex.index(f"% grounded: {fact_ids[-1]}")
    assert idx_last < idx_first


def test_fact_order_with_stale_id_never_drops_a_bullet(master, tailored):
    # BAB-99 doesn't exist -- a deleted/renamed fact shouldn't vanish the
    # entry it never named.
    tex = render_tex(master, tailored, fact_order={"BAB": ["BAB-99"]})
    assert "Authored the first machine-executable" in tex
    assert "Boosted processing throughput" in tex


def test_experience_order_reorders_tailored_entries(master, tailored):
    # master's second experience (Royal Society) isn't in the tailored
    # fixture's selection -- add it so there are two entries to reorder
    tailored.experiences.append(
        TailoredSection(
            ref_id="RS",
            bullets=[TailoredBullet(source_fact_ids=["RS-01"], variants=["x", "x", "x"])],
        )
    )
    tex = render_tex(master, tailored, experience_order=["RS", "BAB"])
    assert tex.index("Royal Society") < tex.index("Babbage")


def test_project_order_reorders_refactor_entries(master):
    second = master.projects[0].model_copy(update={"id": "SECOND", "name": "Second Project"})
    master.projects.append(second)
    tex = render_tex(master, None, project_order=["SECOND", "BERN"])
    assert tex.index("Second Project") < tex.index("Bernoulli Number Generator")


def test_entry_order_with_stale_id_never_drops_an_entry(master):
    tex = render_tex(master, None, experience_order=["NOPE"])
    assert "Babbage" in tex
    assert "Royal Society" in tex


def test_section_order_reorders_top_level_sections(master):
    tex = render_tex(master, None, section_order=["PROJECTS", "EXPERIENCE", "EDUCATION", "SKILLS"])
    assert tex.index("Projects") < tex.index("Experience") < tex.index("Education")


def test_section_order_default_matches_original_layout(master, tailored):
    default_order = render_tex(master, tailored)
    explicit_default = render_tex(
        master, tailored, section_order=["EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS"]
    )
    assert default_order == explicit_default


def test_section_order_with_unknown_key_never_drops_a_section(master):
    tex = render_tex(master, None, section_order=["NOPE", "PROJECTS"])
    assert r"\section{Education}" in tex
    assert r"\section{Experience}" in tex
    assert r"\section{Projects}" in tex
    assert r"\section{Technical Skills}" in tex


def test_injection_in_every_field_is_escaped(master):
    master.name = r"Evil \write18{rm -rf /} & Co"
    master.experiences[0].company = "100% $legit_corp^{tm}"
    tex = render_tex(master, None)
    assert r"\write18" not in tex.replace(r"\textbackslash{}write18", "")
    assert r"\textbackslash{}write18\{rm -rf /\}" in tex
    assert r"100\% \$legit\_corp\textasciicircum{}\{tm\}" in tex
