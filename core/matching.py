"""Deterministic keyword matching for job descriptions.

Keywords themselves are also deterministic: `extract_keywords` below matches
a job posting's text against a fixed, curated dictionary of real CS/tech
terms rather than asking an LLM to judge "the important keywords." An LLM
given the same text twice can legitimately choose a different subset or
phrasing each time (no temperature is pinned, and "normalize this to the
form a resume would use" invites paraphrase, not extraction) -- which made
the match score visibly change across identical re-submissions. A literal,
dictionary-gated match is slower to gain new terms (someone has to add
"Rust" or a new framework by hand) but is reproducible by construction, and
keeps the score to something checkable ("this exact term is or isn't in
the posting"), consistent with the brief's own rule that the match score is
normalized keyword overlap, never the LLM.
"""

import re

from core.schemas import JDExtract, MasterResume

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

# Canonical display form for each recognized term, grouped for readability.
# Not exhaustive -- a deliberately bounded, reviewable list beats an
# LLM guessing, but it does mean a brand-new tool/framework needs to be
# added by hand before it can ever show up as a matched or missing keyword.
SKILLS: list[str] = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl",
    "Haskell", "Elixir", "Dart", "Objective-C", "Bash", "Shell Scripting",
    "SQL", "HTML", "CSS",
    # Frontend
    "React", "Angular", "Vue", "Svelte", "Next.js", "Nuxt.js", "jQuery",
    "Redux", "Tailwind CSS", "Bootstrap", "Sass", "Webpack", "Vite",
    # Backend
    "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring",
    "Spring Boot", "Ruby on Rails", "Laravel", "ASP.NET", ".NET",
    # Databases
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Cassandra",
    "DynamoDB", "Elasticsearch", "Oracle", "SQL Server", "MariaDB",
    "Firebase", "Supabase",
    # Cloud / infra
    "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform",
    "Ansible", "Jenkins", "CircleCI", "GitHub Actions", "CI/CD", "Nginx",
    "Apache", "Linux", "Unix",
    # Tools
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence",
    # ML / AI
    "Machine Learning", "Deep Learning", "Neural Networks",
    "Computer Vision", "Natural Language Processing", "TensorFlow",
    "PyTorch", "Scikit-learn", "Keras", "Pandas", "NumPy", "OpenCV",
    # Concepts / methodologies
    "Agile", "Scrum", "Kanban", "Test-Driven Development", "REST",
    "RESTful APIs", "GraphQL", "gRPC", "Microservices",
    "Object-Oriented Programming", "Functional Programming",
    "Data Structures", "Algorithms", "System Design", "Distributed Systems",
    "Real-time Systems", "Embedded Systems", "Networking", "TCP/IP",
    "HTTP", "JSON", "XML", "YAML", "OAuth", "JWT", "WebSockets",
    # Mobile
    "iOS", "Android", "React Native", "Flutter", "SwiftUI",
    # Testing
    "Unit Testing", "Integration Testing", "Selenium", "Jest", "PyTest",
    "JUnit", "Cypress",
    # Data / other domains
    "Data Engineering", "Data Science", "Big Data", "Spark", "Hadoop",
    "Kafka", "RabbitMQ", "Blockchain", "Cybersecurity", "DevOps",
    "Site Reliability Engineering", "API Design",
]

# Common variant spellings/abbreviations that should count as the canonical
# term on the right when found in JD text -- keeps recall reasonable
# without letting the dictionary itself sprawl into every possible spelling.
ALIASES: dict[str, str] = {
    "postgres": "PostgreSQL",
    "js": "JavaScript",
    "k8s": "Kubernetes",
    "ml": "Machine Learning",
    "nlp": "Natural Language Processing",
    "ci/cd pipelines": "CI/CD",
    "oop": "Object-Oriented Programming",
    "gcp": "Google Cloud",
    "nextjs": "Next.js",
    "vuejs": "Vue",
    "reactjs": "React",
    "golang": "Go",
    "csharp": "C#",
    "dotnet": ".NET",
    "restful": "RESTful APIs",
    "sre": "Site Reliability Engineering",
    "tdd": "Test-Driven Development",
}


def _term_pattern(term: str) -> re.Pattern[str]:
    # Word-boundary via lookaround rather than \b: \b doesn't fire correctly
    # around symbol-only edges (e.g. "C++", "CI/CD", ".NET"), since \b needs
    # a word/non-word transition and punctuation-to-space is non-word on
    # both sides.
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE)


def extract_keywords(text: str) -> list[str]:
    """Which curated skills/CS terms literally appear in `text` -- verbatim
    (case-insensitively) or via a known alias. Deterministic: the same text
    always yields the same list, in the same order, every time."""
    normalized = " ".join(text.split())
    found: list[str] = []
    seen: set[str] = set()
    for term in sorted(SKILLS, key=len, reverse=True):
        if term not in seen and _term_pattern(term).search(normalized):
            found.append(term)
            seen.add(term)
    for alias, canonical in ALIASES.items():
        if canonical not in seen and _term_pattern(alias).search(normalized):
            found.append(canonical)
            seen.add(canonical)
    return found


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def _master_text(master: MasterResume) -> str:
    """Searchable corpus: facts, skills, project names, and project tech.

    Company, title, and coursework are deliberately excluded — a JD keyword
    matching only an employer name is not a skill the candidate claimed.
    """
    facts = " ".join(fact.text for fact in master.fact_lookup().values())
    skills = " ".join(skill for group in master.skills.values() for skill in group)
    projects = " ".join(
        " ".join([project.name, *project.tech]) for project in master.projects
    )
    return " ".join([facts, skills, projects])


def _unique_keywords(keywords: list[str]) -> list[str]:
    return list(dict.fromkeys(keyword for keyword in keywords if keyword.strip()))


def keyword_match(
    jd: JDExtract, master: MasterResume
) -> tuple[float, list[str], list[str]]:
    """Return normalized keyword overlap without using an LLM."""
    resume_tokens = _tokens(_master_text(master))
    matched: list[str] = []
    missing: list[str] = []
    keywords = _unique_keywords(jd.keywords)
    for keyword in keywords:
        keyword_tokens = _tokens(keyword)
        if keyword_tokens and keyword_tokens <= resume_tokens:
            matched.append(keyword)
        else:
            missing.append(keyword)
    score = len(matched) / len(keywords) if keywords else 0.0
    return score, matched, missing
