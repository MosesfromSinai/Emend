"""Dev-only sample data for the seed script — clearly fictional, never demo
marketing content (the landing page's demo content is grounded in the real
sample resume per the brief; this is just local-dev fixture data)."""

from core.schemas import Education, Experience, Fact, MasterResume, Project

SAMPLE_MASTER = MasterResume(
    name="Sam Sample",
    email="sam.sample@example.com",
    phone="555-0100",
    links=["https://github.com/sam-sample"],
    education=[
        Education(
            school="Sample State University",
            degree="B.S. Computer Science",
            location="Springfield, US",
            grad_date="May 2026",
            coursework=["Algorithms", "Databases", "Operating Systems"],
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
                Fact(
                    id="ACME-01",
                    text="Built an internal reporting dashboard used by 3 teams",
                ),
                Fact(
                    id="ACME-02",
                    text="Wrote integration tests covering the billing service",
                ),
                Fact(id="ACME-03", text="Migrated two cron jobs to event-driven tasks"),
            ],
        )
    ],
    projects=[
        Project(
            id="SCHED",
            name="Course Scheduler",
            tech=["Python", "PostgreSQL", "FastAPI"],
            facts=[
                Fact(
                    id="SCHED-01",
                    text="Constraint solver that generates course timetables",
                ),
                Fact(
                    id="SCHED-02", text="REST API with session-scoped saved schedules"
                ),
            ],
        )
    ],
    skills={
        "Languages": ["Python", "TypeScript", "SQL"],
        "Tools": ["Docker", "PostgreSQL", "Git"],
    },
)

SAMPLE_POSTING = """\
Acme Cloud — Backend Engineer (New Grad)

We build developer tools for data teams. You will design and ship REST APIs
in Python, own PostgreSQL schemas and migrations, write tests that keep CI
green, and work with Docker-based deploys. Nice to have: FastAPI, TypeScript,
experience with background job processing.
"""
