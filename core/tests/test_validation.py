import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.schemas import (
    Experience,
    Fact,
    MasterResume,
    Project,
    TailoredBullet,
    TailoredResume,
    TailoredSection,
)
from core.validation import (
    GroundingError,
    build_grounding_report,
    validate,
    validate_grounding,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _one_fact_resume(fact_text: str) -> MasterResume:
    return MasterResume(
        name="Sam Sample",
        email="sam@example.com",
        phone="",
        links=[],
        education=[],
        projects=[],
        skills={},
        experiences=[
            Experience(
                id="ACME",
                company="Acme",
                title="",
                location="",
                start="",
                end="",
                facts=[Fact(id="ACME-01", text=fact_text)],
            )
        ],
    )


def _one_bullet_resume(bullet_text: str) -> TailoredResume:
    return TailoredResume(
        summary_of_strategy="",
        experiences=[
            TailoredSection(
                ref_id="ACME",
                bullets=[
                    TailoredBullet(
                        variants=[bullet_text] * 3, source_fact_ids=["ACME-01"]
                    )
                ],
            )
        ],
        projects=[],
        skills={},
    )


def test_validate_grounding_accepts_known_fact_ids(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored

    validate_grounding(master, tailored)


def test_validate_grounding_rejects_sourceless_bullet(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[0].source_fact_ids = []

    with pytest.raises(GroundingError, match="sourceless bullet"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unknown_fact_id(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[0].source_fact_ids = ["FAKE-99"]

    with pytest.raises(GroundingError, match="unknown fact ids"):
        validate_grounding(master, tailored)


def test_tailored_bullet_rejects_duplicate_source_fact_ids():
    with pytest.raises(ValidationError, match="source_fact_ids must be unique"):
        TailoredBullet(
            variants=["Repeated receipt"] * 3, source_fact_ids=["BAB-01", "BAB-01"]
        )


def test_validate_grounding_rejects_project_fact_on_experience(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[0].source_fact_ids = ["BERN-01"]

    with pytest.raises(GroundingError, match="outside-section ids"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_duplicate_tailored_ref_id(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences.append(tailored.experiences[0].model_copy(deep=True))

    with pytest.raises(GroundingError, match="duplicate section ref_id"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unsupported_numbers(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[1].variants = ["Boosted processing throughput 95%"] * 3

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unsupported_plus_numbers(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[0].variants = [
        "Authored the first algorithm for 20+ users"
    ] * 3

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_accepts_supported_plus_numbers(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[0].variants = ["Documented the module for 100+ users"] * 3
    tailored.experiences[0].bullets[0].source_fact_ids = ["BAB-03"]

    validate_grounding(master, tailored)


def test_validate_grounding_rejects_low_fact_overlap(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[0].variants = [
        "Led Kubernetes migrations for payment systems"
    ] * 3

    with pytest.raises(GroundingError, match="low fact overlap"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unsupported_skill(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.skills["Tools"].append("Kubernetes")

    with pytest.raises(GroundingError, match="unsupported skills"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_unknown_skill_category(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.skills["Cloud"] = ["AWS"]

    with pytest.raises(GroundingError, match="unknown skill category"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_skill_moved_to_wrong_category(
    sample_master, sample_tailored
):
    # "Python" is a real master skill, but only under "Languages" -- filing it
    # under "Tools" instead must still be rejected, even though "python" is
    # present somewhere in the master skills as a whole.
    master, tailored = sample_master, sample_tailored
    tailored.skills["Tools"].append("Python")

    with pytest.raises(GroundingError, match="unsupported skills"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_derived_percentage():
    # "80%" is computed from 45 and 10 (a ~78% reduction, rounded up) -- the
    # fact only ever states the two absolute minute values, never a percent.
    master = _one_fact_resume("Cut deploy time from 45 minutes to under 10")
    tailored = _one_bullet_resume("Cut deploy time by 80%, down to under 10 minutes.")

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_rejects_subtraction_delta():
    # "35" is 45 minus 10 -- a derived delta, not a number either fact states.
    master = _one_fact_resume("Cut deploy time from 45 minutes to under 10")
    tailored = _one_bullet_resume("Reduced deploy time by 35 minutes, from 45 down to under 10.")

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_accepts_number_copied_from_fact():
    # 45 and 10 both appear literally in the fact -- no arithmetic performed.
    master = _one_fact_resume("Cut deploy time from 45 minutes to under 10")
    tailored = _one_bullet_resume("Cut deploy time from 45 minutes to under 10.")

    validate_grounding(master, tailored)


def test_validate_grounding_rejects_unit_magnitude_swap():
    # Same digits, different unit -- "20 ms" restated as "20 seconds" is a
    # 1000x magnitude inflation that a bare-digit comparison would miss.
    master = _one_fact_resume("Reduced p95 latency by 20 ms.")
    tailored = _one_bullet_resume("Reduced p95 latency by 20 seconds.")

    with pytest.raises(GroundingError, match="unsupported numbers"):
        validate_grounding(master, tailored)


def test_validate_grounding_accepts_same_unit_paraphrase():
    # Restating the unit's spelling without changing its magnitude (secs ->
    # seconds) is a paraphrase, not a swap, and should still pass.
    master = _one_fact_resume("Reduced p95 latency by 20 secs.")
    tailored = _one_bullet_resume("Reduced p95 latency by 20 seconds.")

    validate_grounding(master, tailored)


def test_fact_lookup_rejects_duplicate_fact_ids(sample_master):
    master = sample_master
    master.experiences[1].facts[0].id = "BAB-01"

    with pytest.raises(ValueError, match="duplicate fact id"):
        master.fact_lookup()


def test_fact_rejects_invalid_id_format():
    with pytest.raises(ValidationError, match="fact id must match"):
        Fact(id="bad-id", text="Not a valid grounded fact id")


def test_fact_rejects_text_over_the_input_char_cap():
    # PUT /resumes/master takes a MasterResume straight from the client --
    # unlike LLM/parsed text, this field had no upstream length limit of its
    # own before this cap, so a client could submit an arbitrarily long
    # bullet bounded only by the API's overall body-size middleware.
    from core.config import max_input_chars

    with pytest.raises(ValidationError, match="at most"):
        Fact(id="ACME-01", text="x" * (max_input_chars() + 1))


def test_experience_title_rejects_text_over_the_input_char_cap():
    # Same gap as Fact.text, but on a sibling free-text field -- the fix
    # applies a shared BoundedText type, so this must catch it too.
    from core.config import max_input_chars

    with pytest.raises(ValidationError, match="at most"):
        Experience(
            id="ACME",
            company="Acme",
            title="x" * (max_input_chars() + 1),
            location="",
            start="",
            end="",
            facts=[],
        )


def test_project_tech_item_rejects_text_over_the_input_char_cap():
    # Same gap as Fact.text/Experience.title, but on a list-of-strings
    # field -- a single oversized item inside the list, not the list
    # itself, is what BoundedText must catch here.
    from core.config import max_input_chars

    with pytest.raises(ValidationError, match="at most"):
        Project(id="ACME", name="Acme", tech=["x" * (max_input_chars() + 1)], facts=[])


def test_master_resume_rejects_invalid_section_id():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    data["experiences"][0]["id"] = "bad-id"

    with pytest.raises(ValidationError, match="section id must be uppercase"):
        MasterResume(**data)


def test_master_resume_rejects_duplicate_section_ids():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    data["projects"][0]["id"] = "BAB"
    data["projects"][0]["facts"][0]["id"] = "BAB-04"
    data["projects"][0]["facts"][1]["id"] = "BAB-05"

    with pytest.raises(ValidationError, match="duplicate section id"):
        MasterResume(**data)


def test_master_resume_rejects_fact_id_outside_section_prefix():
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    data["experiences"][0]["facts"][0]["id"] = "RS-01"

    with pytest.raises(ValidationError, match="fact ids must start with section id"):
        MasterResume(**data)


def test_master_resume_rejects_duplicate_fact_id_within_one_section():
    # fact_lookup() already catches a duplicate across the whole resume, but
    # only lazily, whenever something downstream calls it -- construction
    # itself should reject it immediately with a clean validation error.
    data = json.loads((FIXTURES / "sample_master.json").read_text())
    data["experiences"][0]["facts"][1]["id"] = data["experiences"][0]["facts"][0]["id"]

    with pytest.raises(ValidationError, match="duplicate fact id within section"):
        MasterResume(**data)


def test_build_grounding_report_marks_valid_bullets_supported(sample_tailored):
    tailored = sample_tailored

    report = build_grounding_report(tailored, 0.5, ["Python"], ["Kubernetes"])
    bullet_count = sum(
        len(section.bullets) for section in [*tailored.experiences, *tailored.projects]
    )

    assert report.match_score == 0.5
    assert report.matched_keywords == ["Python"]
    assert report.missing_keywords == ["Kubernetes"]
    assert report.grounding_ok is True
    assert len(report.verdicts) == bullet_count
    assert all(verdict.supported for verdict in report.verdicts)


def test_verdicts_carry_source_fact_ids(sample_tailored):
    # the provenance panel reads these; without them it would have to parse
    # `% grounded:` comments out of the rendered tex
    tailored = sample_tailored

    report = build_grounding_report(tailored, 0.0, [], [])
    cited = [
        bullet.source_fact_ids
        for section in [*tailored.experiences, *tailored.projects]
        for bullet in section.bullets
    ]

    assert [verdict.source_fact_ids for verdict in report.verdicts] == cited
    assert all(verdict.source_fact_ids for verdict in report.verdicts)


def test_validate_bridge_returns_supported_verdicts(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored

    grounding_ok, verdicts = validate(master, tailored)

    assert grounding_ok is True
    assert all(verdict.supported for verdict in verdicts)
    assert all(verdict.source_fact_ids for verdict in verdicts)


def test_validate_bridge_returns_failure_verdict(sample_master, sample_tailored):
    master, tailored = sample_master, sample_tailored
    tailored.experiences[0].bullets[0].source_fact_ids = []

    grounding_ok, verdicts = validate(master, tailored)

    assert grounding_ok is False
    assert verdicts[0].supported is False
    assert "sourceless bullet" in verdicts[0].reason
