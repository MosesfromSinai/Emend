import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api import core_bridge
from api import db as db_module
from api.db import Base
from api.main import app
from core.schemas import (
    BulletVerdict,
    Education,
    Experience,
    Fact,
    JDExtract,
    MasterResume,
    Project,
    Report,
    TailoredBullet,
    TailoredResume,
    TailoredSection,
)

FAKE_TEX = """\\documentclass{article}
% grounded: ACME-01, ACME-02
\\begin{document}Sam Sample\\end{document}
"""


class _FakeStreamResponse:
    """Minimal stand-in for httpx.stream()'s context-managed Response --
    core_bridge.fetch_jd_text streams (not httpx.get) so an oversized
    response can be capped mid-download rather than only after it's
    already fully buffered."""

    is_redirect = False
    encoding = "utf-8"

    def __init__(self, text, headers=None):
        self._text = text
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        pass

    def iter_bytes(self):
        yield self._text.encode("utf-8")


def _fake_stream(text, headers=None):
    return lambda method, url, **kwargs: _FakeStreamResponse(text, headers)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """api.rate_limit._calls is a module-level dict, not request-scoped, so
    it otherwise persists for the whole pytest run -- and TestClient reports
    the same client host for every test, so an IP-keyed bucket (e.g.
    new-session creation) would silently accumulate hits across unrelated
    tests instead of resetting per test the way the DB (db_engine) does."""
    from api.rate_limit import _calls

    _calls.clear()
    yield
    _calls.clear()


@pytest.fixture()
def db_engine(tmp_path, monkeypatch):
    """File-backed SQLite per test; api.db.SessionLocal is swapped in place
    (all app code resolves it as a module attribute at call time)."""
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", factory)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(db_engine, tmp_path, monkeypatch):
    from api.config import settings

    monkeypatch.setattr(settings, "artifacts_dir", str(tmp_path / "artifacts"))
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def other_client(db_engine):
    """A second visitor: same app + DB, separate cookie jar."""
    with TestClient(app) as c:
        yield c


def sample_master() -> MasterResume:
    return MasterResume(
        name="Sam Sample",
        email="sam@example.com",
        phone="555-0100",
        links=["https://example.com/sam"],
        education=[
            Education(
                school="Sample State University",
                degree="B.S. Computer Science",
                location="Springfield, US",
                grad_date="May 2026",
                coursework=["Algorithms", "Databases"],
            )
        ],
        experiences=[
            Experience(
                id="ACME",
                company="Acme Corp",
                title="Software Engineering Intern",
                location="Remote",
                start="Jun 2025",
                end="Aug 2025",
                facts=[
                    Fact(id="ACME-01", text="Built an internal reporting dashboard"),
                    Fact(
                        id="ACME-02",
                        text="Wrote integration tests for the billing service",
                    ),
                ],
            )
        ],
        projects=[
            Project(
                id="PROJ",
                name="Course Scheduler",
                tech=["Python", "PostgreSQL"],
                facts=[
                    Fact(id="PROJ-01", text="Constraint solver for course timetables")
                ],
            )
        ],
        skills={"Languages": ["Python", "SQL"], "Tools": ["Docker"]},
    )


@pytest.fixture()
def master() -> MasterResume:
    return sample_master()


@pytest.fixture()
def pipeline(monkeypatch, tmp_path):
    """Stub every core/latex call at the bridge seam and record invocations."""
    calls = []

    def parse_jd(text):
        calls.append("parse_jd")
        return JDExtract(
            company="Acme Cloud",
            title="Backend Engineer",
            hard_skills=["python", "postgresql"],
            soft_requirements=["ownership"],
            responsibilities=["ship REST APIs"],
            keywords=["python", "postgresql", "kubernetes"],
        )

    def keyword_match(jd, master):
        calls.append("keyword_match")
        return 0.82, ["python", "postgresql"], ["kubernetes"]

    def tailor(master, jd):
        calls.append("tailor")
        return TailoredResume(
            summary_of_strategy="Lead with backend work",
            experiences=[
                TailoredSection(
                    ref_id="ACME",
                    bullets=[
                        TailoredBullet(
                            variants=["Built a reporting dashboard"] * 3,
                            source_fact_ids=["ACME-01"],
                        )
                    ],
                )
            ],
            projects=[],
            skills={"Languages": ["Python"]},
        )

    def validate(master, tailored, match_score, matched_keywords, missing_keywords):
        calls.append("validate")
        return Report(
            match_score=match_score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            grounding_ok=True,
            verdicts=[
                BulletVerdict(
                    bullet="Built a reporting dashboard",
                    supported=True,
                    reason="cites ACME-01",
                )
            ],
        )

    def render_and_compile(master, tailored, *_args, **_kwargs):
        calls.append("render_and_compile")
        # Nested in its own subdir, not tmp_path itself -- mirrors the real
        # compile_tex(), which hands back a path inside a dedicated temp dir
        # (not the caller's directory), so callers that clean up that dir
        # after copying the PDF out exercise the same shape here.
        artifact_dir = tmp_path / "artifact"
        artifact_dir.mkdir(exist_ok=True)
        pdf = artifact_dir / "out.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        return FAKE_TEX, str(pdf), "compile ok"

    for name, fn in [
        ("parse_jd", parse_jd),
        ("keyword_match", keyword_match),
        ("tailor", tailor),
        ("validate", validate),
        ("render_and_compile", render_and_compile),
    ]:
        monkeypatch.setattr(core_bridge, name, fn)
    return calls


def new_uuid() -> str:
    return str(uuid.uuid4())
