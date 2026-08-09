import pytest

from core.schemas import CustomEntry, CustomSection, Fact, TailoredBullet, TailoredSection
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


def test_fact_order_with_duplicate_id_never_renders_twice(master):
    # a duplicate id in an order list (client-side reorder bug, a replayed
    # request) must not duplicate the bullet in the rendered output
    tex = render_tex(master, None, fact_order={"BAB": ["BAB-01", "BAB-02", "BAB-01"]})
    assert tex.count("Wrote the first published algorithm") == 1


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


def test_custom_section_renders_bullets_and_bare_entry(master):
    custom = master.model_copy(
        update={
            "custom_sections": [
                CustomSection(
                    key="RESEARCH",
                    heading="Research Experience",
                    entries=[
                        CustomEntry(
                            id="RES",
                            title="Research Assistant",
                            subtitle="UCSD Bio Lab",
                            facts=[Fact(id="RES-01", text="Ran assays weekly.")],
                        )
                    ],
                ),
                CustomSection(
                    key="CERTIF",
                    heading="Certifications",
                    entries=[
                        CustomEntry(id="CERT", title="AWS Certified Solutions Architect", end="2023")
                    ],
                ),
            ]
        }
    )
    tex = render_tex(custom, None)
    assert r"\section{Research Experience}" in tex
    assert "Ran assays weekly." in tex
    assert r"\section{Certifications}" in tex
    assert "AWS Certified Solutions Architect" in tex
    # a bulletless entry never emits an empty itemize
    certifications_start = tex.index(r"\section{Certifications}")
    certifications_body = tex[certifications_start : tex.index(r"\end{document}")]
    assert r"\resumeItemListStart" not in certifications_body


def test_section_order_reorders_a_custom_section(master):
    custom = master.model_copy(
        update={
            "custom_sections": [
                CustomSection(
                    key="RESEARCH",
                    heading="Research Experience",
                    entries=[CustomEntry(id="RES", title="Research Assistant")],
                )
            ]
        }
    )
    tex = render_tex(custom, None, section_order=["RESEARCH", "EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS"])
    assert tex.index("Research Experience") < tex.index("Education")


def test_excluded_facts_drops_a_bullet(master, tailored):
    tex = render_tex(master, tailored, excluded_facts=["BAB-01"])
    assert "Authored the first machine-executable" not in tex
    assert "Boosted processing throughput" in tex  # BAB-02 wasn't excluded


def test_excluded_facts_drops_a_refactor_bullet_only(master):
    tex = render_tex(master, None, excluded_facts=["BAB-01"])
    assert "Wrote the first published algorithm" not in tex
    assert "Improved punch-card throughput" in tex


def test_excluded_experiences_drops_a_whole_entry(master):
    tex = render_tex(master, None, excluded_experiences=["RS"])
    assert "Royal Society" not in tex
    assert "Babbage" in tex


def test_excluded_projects_drops_a_whole_entry(master):
    tex = render_tex(master, None, excluded_projects=["BERN"])
    assert r"\section{Projects}" not in tex


def test_excluding_all_bullets_still_renders_the_entry(master):
    # BAB has 3 facts; deleting all of them leaves an empty bullet list but
    # the entry (title/company/dates) still renders -- deleting content
    # isn't the same as deleting the entry itself
    tex = render_tex(master, None, excluded_facts=["BAB-01", "BAB-02", "BAB-03"])
    assert "Babbage" in tex
    assert "Wrote the first published algorithm" not in tex


def test_override_replaces_header_fields(master):
    tex = render_tex(master, None, text_overrides={"name": "Ada L. Byron", "phone": "555-9999"})
    assert r"Ada L. Byron" in tex
    assert "555-9999" in tex
    assert "Ada Lovelace" not in tex


def test_override_replaces_link_display(master):
    tex = render_tex(master, None, text_overrides={"link:0": "linkedin.com/in/countess-lovelace"})
    assert "countess-lovelace" in tex


def test_clearing_phone_omits_it_without_stray_separator(master):
    tex = render_tex(master, None, text_overrides={"phone": ""})
    assert master.phone not in tex
    assert master.email in tex
    header = tex[tex.index(r"\small") : tex.index(r"\end{center}")]
    assert not header.strip().startswith("$|$")


def test_clearing_a_link_omits_only_that_one(master):
    tex = render_tex(master, None, text_overrides={"link:0": ""})
    header = tex[tex.index(r"\small") : tex.index(r"\end{center}")]
    assert "ada-lovelace" not in header
    assert "adal" in header
    assert header.count("$|$") == 2  # phone, email, remaining link -> 2 joins


def test_clearing_email_and_phone_leaves_only_links(master):
    tex = render_tex(master, None, text_overrides={"email": "", "phone": ""})
    header = tex[tex.index(r"\small") : tex.index(r"\end{center}")]
    assert master.email not in header
    assert master.phone not in header
    assert "ada-lovelace" in header


def test_override_replaces_experience_structural_fields(master):
    tex = render_tex(master, None, text_overrides={
        "experience:BAB:company": "Analytical Engines Ltd",
        "experience:BAB:title": "Lead Engineer",
    })
    assert "Analytical Engines Ltd" in tex
    assert "Lead Engineer" in tex
    assert "Babbage \\& Co" not in tex


def test_override_replaces_experience_dates(master):
    tex = render_tex(master, None, text_overrides={
        "experience:BAB:start": "Jan 2024",
        "experience:BAB:end": "Present",
    })
    assert "Jan 2024 -- Present" in tex
    assert "Jun 2023 -- Aug 2023" not in tex


def test_override_applies_in_tailor_mode_too(master, tailored):
    tex = render_tex(master, tailored, text_overrides={"experience:BAB:company": "Renamed Co"})
    assert "Renamed Co" in tex


def test_override_replaces_project_fields(master):
    tex = render_tex(master, None, text_overrides={
        "project:BERN:name": "Bernoulli Calculator",
        "project:BERN:tech": "Python, NumPy",
    })
    assert "Bernoulli Calculator" in tex
    assert "Python, NumPy" in tex


def test_override_replaces_education_fields(master):
    tex = render_tex(master, None, text_overrides={
        "education:0:school": "Cambridge University",
        "education:0:coursework": "Custom Course A, Custom Course B",
    })
    assert "Cambridge University" in tex
    assert "Custom Course A, Custom Course B" in tex


def test_override_can_clear_coursework(master):
    tex = render_tex(master, None, text_overrides={"education:0:coursework": ""})
    assert "Relevant Coursework" not in tex


def test_override_can_add_coursework_where_none_existed(master):
    master.education[0].coursework = []
    tex = render_tex(master, None, text_overrides={"education:0:coursework": "New Course"})
    assert "Relevant Coursework" in tex
    assert "New Course" in tex


def test_override_replaces_skills_category_text(master):
    tex = render_tex(master, None, text_overrides={"skills:Languages": "Ada, Python, Rust"})
    assert r"\textbf{Languages}{: Ada, Python, Rust}" in tex
    assert "Assembly" not in tex


def test_override_renames_a_section_heading(master):
    tex = render_tex(master, None, text_overrides={"section:EXPERIENCE:heading": "Leadership"})
    assert r"\section{Leadership}" in tex
    assert r"\section{Experience}" not in tex


def test_unknown_override_keys_are_ignored(master):
    tex = render_tex(master, None, text_overrides={"experience:NOPE:company": "Ghost Corp"})
    assert "Ghost Corp" not in tex
    assert "Babbage" in tex


def test_injection_in_every_field_is_escaped(master):
    master.name = r"Evil \write18{rm -rf /} & Co"
    master.experiences[0].company = "100% $legit_corp^{tm}"
    tex = render_tex(master, None)
    assert r"\write18" not in tex.replace(r"\textbackslash{}write18", "")
    assert r"\textbackslash{}write18\{rm -rf /\}" in tex
    assert r"100\% \$legit\_corp\textasciicircum{}\{tm\}" in tex
