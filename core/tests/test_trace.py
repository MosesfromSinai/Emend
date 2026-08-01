import json

from core.trace import record_call, trace_path


def test_trace_disabled_by_default(monkeypatch):
    monkeypatch.delenv("EMEND_TRACE_PATH", raising=False)

    assert trace_path() is None
    record_call(label="x", model="m", input_tokens=1, output_tokens=1)  # no-op, no error


def test_record_call_appends_jsonl(tmp_path, monkeypatch):
    path = tmp_path / "traces" / "run.jsonl"
    monkeypatch.setenv("EMEND_TRACE_PATH", str(path))

    record_call(label="structure_resume", model="m1", input_tokens=10, output_tokens=20)
    record_call(label="parse_jd", model="m2", input_tokens=5, output_tokens=7)

    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert [entry["label"] for entry in lines] == ["structure_resume", "parse_jd"]
    assert lines[0]["input_tokens"] == 10
    assert lines[0]["cache_read_input_tokens"] == 0
