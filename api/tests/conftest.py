import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api import db as db_module
from api.db import Base
from api.main import app
from core.schemas import Education, Experience, Fact, MasterResume, Project


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


def new_uuid() -> str:
    return str(uuid.uuid4())
