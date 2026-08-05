"""Real-mode (MOCK=0) tests.

No network: a fake client records the outgoing request so we can assert on the
request shape, which is where the contract with Anthropic actually lives.
"""

from types import SimpleNamespace

import pytest

from core.llm import (
    FAST_MODEL,
    TAILOR_MODEL,
    LLMUnavailableError,
    StructuredResult,
    structured_call,
    structured_tool,
    supports_strict_tool,
)
from core.pipeline import parse_jd, real_tailor_result, structure_resume, tailor
from core.schemas import (
    BulletVerdict,
    JDExtract,
    MasterResume,
    TailoredResume,
)
from core.validation import GroundingError, judge_bullets


@pytest.fixture(autouse=True)
def real_mode(monkeypatch):
    monkeypatch.setenv("MOCK", "0")


def _jd() -> JDExtract:
    return JDExtract(
        company="Acme",
        title="Engineer",
        hard_skills=["Python"],
        soft_requirements=[],
        responsibilities=[],
        keywords=["Python"],
    )


class FakeClient:
    """Records requests and replays queued tool-use payloads."""

    def __init__(self, *payloads: dict):
        self.payloads = list(payloads)
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        payload = self.payloads.pop(0) if len(self.payloads) > 1 else self.payloads[0]
        block = SimpleNamespace(type="tool_use", name="emit_schema", input=payload)
        usage = SimpleNamespace(
            input_tokens=10,
            output_tokens=20,
            cache_read_input_tokens=5,
            cache_creation_input_tokens=0,
        )
        return SimpleNamespace(content=[block], usage=usage)


def _tailored_payload(master: MasterResume) -> dict:
    return TailoredResume(
        summary_of_strategy="Lead with Python work.",
        experiences=[
            {
                "ref_id": e.id,
                "bullets": [
                    {"variants": [f.text] * 3, "source_fact_ids": [f.id]} for f in e.facts
                ],
            }
            for e in master.experiences
        ],
        projects=[
            {
                "ref_id": p.id,
                "bullets": [
                    {"variants": [f.text] * 3, "source_fact_ids": [f.id]} for f in p.facts
                ],
            }
            for p in master.projects
        ],
        skills=master.skills,
    ).model_dump()


# --- request shape -----------------------------------------------------------


def test_structure_resume_uses_fast_model_and_caches_system():
    # the LLM returns facts with no ids -- core assigns those after
    raw_payload = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "555-010-1010",
        "links": ["linkedin.com/in/ada-lovelace"],
        "education": [],
        "experiences": [
            {
                "company": "Babbage & Co",
                "title": "Software Engineer Intern",
                "location": "London, UK",
                "start": "Jun 2023",
                "end": "Aug 2023",
                "facts": [
                    {"text": "Wrote the first published algorithm intended for machine execution."}
                ],
            }
        ],
        "projects": [],
        "skills": {"Languages": ["Ada"]},
    }
    client = FakeClient(raw_payload)

    master = structure_resume("messy resume text", client=client)

    assert master.name == "Ada Lovelace"
    assert master.experiences[0].company == "Babbage & Co"
    assert master.experiences[0].facts[0].id.endswith("-01")

    call = client.calls[0]
    assert call["model"] == FAST_MODEL
    assert call["system"][-1]["cache_control"] == {"type": "ephemeral"}
    assert call["tool_choice"] == {"type": "tool", "name": "emit_schema"}


def test_parse_jd_uses_fast_model():
    jd = _jd()
    client = FakeClient(jd.model_dump())

    assert (
        parse_jd(
            "We need a Python engineer to join our growing backend team.",
            client=client,
        )
        == jd
    )
    assert client.calls[0]["model"] == FAST_MODEL


def test_tailor_uses_sonnet_and_caches_the_master_resume(sample_master):
    master = sample_master
    client = FakeClient(_tailored_payload(master))

    tailor(master, _jd(), client=client)

    call = client.calls[0]
    assert call["model"] == TAILOR_MODEL
    # master resume rides in the cached prefix so repeat tailoring reuses it
    assert master.experiences[0].facts[0].text in call["system"][-1]["text"]
    assert call["system"][-1]["cache_control"] == {"type": "ephemeral"}


# --- the guarantee -----------------------------------------------------------


def test_tailor_rejects_output_citing_unknown_fact_ids(sample_master):
    master = sample_master
    payload = _tailored_payload(master)
    payload["experiences"][0]["bullets"][0]["source_fact_ids"] = ["ZZ-99"]

    with pytest.raises(GroundingError):
        tailor(master, _jd(), client=FakeClient(payload))


def test_tailor_rejects_output_inventing_numbers(sample_master):
    master = sample_master
    payload = _tailored_payload(master)
    payload["experiences"][0]["bullets"][0]["variants"][0] += " across 47 teams"

    with pytest.raises(GroundingError):
        tailor(master, _jd(), client=FakeClient(payload))


def test_tailor_retries_a_grounding_failure_with_the_violation_fed_back(sample_master):
    # one invented number in an otherwise-fine draft shouldn't fail the
    # whole job -- the model gets told exactly what was rejected and retries
    master = sample_master
    bad_payload = _tailored_payload(master)
    bad_payload["experiences"][0]["bullets"][0]["variants"][0] += " across 47 teams"
    good_payload = _tailored_payload(master)
    client = FakeClient(bad_payload, good_payload)

    result = tailor(master, _jd(), client=client)

    assert result == TailoredResume(**good_payload)
    assert len(client.calls) == 2
    assert "47" in client.calls[1]["messages"][-1]["content"]


def test_real_tailor_result_reports_judge_verdicts(sample_master):
    master = sample_master
    tailored_payload = _tailored_payload(master)
    unsupported = BulletVerdict(
        bullet="", supported=False, reason="Claims scope the facts do not support."
    ).model_dump()
    client = FakeClient(tailored_payload, unsupported)

    _tailored, report = real_tailor_result(master, _jd(), client=client)

    assert report.grounding_ok is False
    assert report.verdicts and all(not v.supported for v in report.verdicts)
    # verdicts carry our bullet text, not the model's echo
    assert all(v.bullet for v in report.verdicts)
    assert report.match_score == 1.0


def test_judge_runs_once_per_variant_on_the_fast_model(sample_master):
    master = sample_master
    tailored = TailoredResume(**_tailored_payload(master))
    supported = BulletVerdict(bullet="", supported=True, reason="Traceable.").model_dump()
    client = FakeClient(supported)

    verdicts = judge_bullets(master, tailored, client=client)

    bullet_count = sum(
        len(s.bullets) for s in [*tailored.experiences, *tailored.projects]
    )
    # one verdict per bullet, but every one of its 3 variants got judged
    assert len(verdicts) == bullet_count
    assert len(client.calls) == bullet_count * 3
    assert {call["model"] for call in client.calls} == {FAST_MODEL}


def test_exported_validate_judges_in_real_mode(monkeypatch, sample_master):
    """api/core_bridge.py resolves `core.validate` — it must reach the judge."""
    import core
    import core.validation as validation

    master = sample_master
    tailored = TailoredResume(**_tailored_payload(master))
    seen: list[str] = []

    def fake_structured_call(model, system, user, schema, **kwargs):
        seen.append(model)
        return StructuredResult(BulletVerdict(bullet="", supported=True, reason="Traceable."))

    monkeypatch.setattr(validation, "structured_call_with_usage", fake_structured_call)

    grounding_ok, verdicts = core.validate(master, tailored)

    assert grounding_ok is True
    assert verdicts and all(v.supported for v in verdicts)
    assert seen and set(seen) == {FAST_MODEL}
    # the reason is the judge's, not the deterministic placeholder
    assert "deterministic" not in verdicts[0].reason.lower()


def test_exported_validate_short_circuits_before_spending_judge_calls(monkeypatch, sample_master):
    import core
    import core.validation as validation

    master = sample_master
    payload = _tailored_payload(master)
    payload["experiences"][0]["bullets"][0]["source_fact_ids"] = ["ZZ-99"]
    calls: list[str] = []
    monkeypatch.setattr(
        validation,
        "structured_call_with_usage",
        lambda *a, **k: calls.append("called"),
    )

    grounding_ok, verdicts = core.validate(master, TailoredResume(**payload))

    assert grounding_ok is False
    assert calls == []
    assert not verdicts[0].supported


# --- strict tool use ---------------------------------------------------------


def test_strict_is_enabled_for_flat_schemas():
    assert supports_strict_tool(JDExtract)
    assert supports_strict_tool(BulletVerdict)
    tool = structured_tool(JDExtract, strict=True)
    assert tool["strict"] is True
    assert tool["input_schema"]["additionalProperties"] is False


def test_strict_is_refused_for_schemas_with_open_maps():
    # skills: dict[str, list[str]] renders additionalProperties as a schema,
    # which strict tool use rejects.
    assert not supports_strict_tool(MasterResume)
    assert not supports_strict_tool(TailoredResume)
    assert "strict" not in structured_tool(MasterResume)


def test_structured_tool_does_not_mutate_the_model_schema():
    before = JDExtract.model_json_schema()
    structured_tool(JDExtract, strict=True)
    assert JDExtract.model_json_schema() == before


# --- retry -------------------------------------------------------------------


def _raw_payload_with_fact(fact_text: str) -> dict:
    return {
        "name": "Ada Lovelace",
        "email": "",
        "phone": "",
        "links": [],
        "education": [],
        "experiences": [
            {
                "company": "Babbage & Co",
                "title": "Engineer",
                "location": "London, UK",
                "start": "Jun 2023",
                "end": "Aug 2023",
                "facts": [{"text": fact_text}],
            }
        ],
        "projects": [],
        "skills": {},
    }


def test_structure_repair_retry_calls_out_a_segmentation_failure():
    # a leaked header, not a stray fragment -- the retry has to say so
    leaked = _raw_payload_with_fact("Technical Lead Jun 2025 - Aug 2025")
    clean = _raw_payload_with_fact("Wrote the first published algorithm.")
    client = FakeClient(leaked, clean)

    structure_resume("messy resume text", client=client)

    retry = client.calls[1]["messages"][0]["content"]
    assert "entry boundaries in the wrong place" in retry
    assert "starts a NEW entry" in retry


def test_structure_repair_retry_stays_plain_for_an_ordinary_fragment():
    fragment = _raw_payload_with_fact("and validated the results.")
    clean = _raw_payload_with_fact("Wrote the first published algorithm.")
    client = FakeClient(fragment, clean)

    structure_resume("messy resume text", client=client)

    retry = client.calls[1]["messages"][0]["content"]
    assert "Fix these specific facts" in retry
    assert "entry boundaries" not in retry


def test_structured_call_retries_once_on_invalid_output():
    jd = _jd()
    client = FakeClient({"company": "Acme"}, jd.model_dump())

    assert structured_call("m", "s", "u", JDExtract, client=client) == jd
    assert len(client.calls) == 2
    # the retry tells the model what it got wrong
    assert "failed schema validation" in client.calls[1]["messages"][0]["content"]


def test_structured_call_raises_after_exhausting_retries():
    client = FakeClient({"company": "Acme"})

    with pytest.raises(LLMUnavailableError, match="invalid JDExtract"):
        structured_call("m", "s", "u", JDExtract, client=client, retries=1)
    assert len(client.calls) == 2
