"""The core pipeline: deterministic under MOCK=1, real Anthropic calls under MOCK=0.

Both modes return the same Pydantic types and both pass generated content
through `validate_grounding` before returning it, so the no-invented-claims
guarantee does not depend on which mode is running.
"""

import json
import re
from typing import Any

from pydantic import BaseModel, ValidationError

from core.config import max_input_chars, mock_enabled
from core.llm import (
    FAST_MODEL,
    TAILOR_MODEL,
    cacheable_system,
    structured_call_with_usage,
)
from core.matching import keyword_match
from core.normalize import (
    BULLET_START_PATTERN,
    reattach_orphan_dates,
    split_inline_bullets,
    unwrap_text,
)
from core.prompts import PARSE_JD_SYSTEM, STRUCTURE_SYSTEM, TAILOR_SYSTEM
from core.schemas import (
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
from core.trace import record_call
from core.validation import build_grounding_report, judge_bullets, validate_grounding

JD_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#]*(?:[.-][A-Za-z0-9+#]+)*")
JD_STOP_WORDS = {"and", "for", "the", "to", "using", "with"}
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"\(?\+?\d[\d\s().-]{7,}\d")
LINK_PATTERN = re.compile(r"(?:https?://|www\.|linkedin\.com/|github\.com/)\S+")
BULLET_PATTERN = re.compile(r"^[•\-*·]+\s*")
MAX_FACTS_PER_SECTION = 99  # fact ids carry a two-digit suffix
SECTION_HEADER_PATTERN = re.compile(
    r"^(?:work |professional |relevant )?experiences?:?$"
    r"|^educations?:?$"
    r"|^(?:technical |core )?skills:?$"
    r"|^projects?:?$"
    r"|^summary:?$"
    r"|^objective:?$"
    r"|^certifications?:?$"
    r"|^awards?:?$"
    r"|^publications?:?$",
    re.IGNORECASE,
)

# -- entity-id derivation ------------------------------------------------

ENTITY_STOP_WORDS = {"a", "an", "and", "at", "the", "of", "for"}
ENTITY_WORD_PATTERN = re.compile(r"[A-Za-z0-9]+")
CAMEL_PART_PATTERN = re.compile(r"[A-Z][a-z0-9]*|[a-z0-9]+")
MIN_CAMEL_PART = 3
MAX_PREFIX_LEN = 6

# -- entry-header parsing --------------------------------------------------

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
DATE_RANGE_PATTERN = re.compile(
    r"(?P<range>(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{1,2}/\d{4})\s*-\s*"
    r"(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{1,2}/\d{4}|Present|Current))",
    re.IGNORECASE,
)
# "<org>, <city>, ST" -- a comma between the two settles the split outright
COMMA_LOCATION_PATTERN = re.compile(
    r"^(?P<head>.+?[^\s,]),\s*(?P<loc>[A-Z][a-zA-Z.]*(?:\s+[A-Z][a-zA-Z.]*)?,\s*[A-Z]{2})\s*$"
)
# no separating comma: longest city form first, falling back to the shorter
# one when the longer reading would cut inside the organization's own name
LOCATION_SUFFIX_PATTERNS = (
    re.compile(r"(?:^|\s)([A-Z][a-zA-Z.]*\s+[A-Z][a-zA-Z.]*,\s*[A-Z]{2})\s*$"),
    re.compile(r"(?:^|\s)([A-Z][a-zA-Z.]*,\s*[A-Z]{2})\s*$"),
)
BARE_YEAR_PATTERN = re.compile(r"(?:^|\s)((?:19|20)\d{2})\s*$")
# a remainder left dangling on a connector means the location split cut
# inside the organization's own name, not between the name and its city
DANGLING_TAIL_PATTERN = re.compile(r"(?:[,&@/|-]|\b(?:of|the|at|and|for|de))$", re.IGNORECASE)
# a "city" starting with one of these is really the tail of the org's name
# ("Riverside State University Riverside, CA" is not in University Riverside)
ORG_TAIL_WORDS = {
    "university", "college", "institute", "school", "academy", "consortium",
    "corp", "corporation", "inc", "llc", "ltd", "company", "group", "foundation",
    "systems", "technologies", "labs", "laboratory", "center", "centre", "hospital",
}
GRAD_DATE_PATTERN = re.compile(
    r"(?:expected\s+)?(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{4})\s*$", re.IGNORECASE
)
COURSEWORK_PATTERN = re.compile(r"^(?:relevant\s+)?coursework\s*:\s*(.+)$", re.IGNORECASE)

# -- non-fact structured lines -------------------------------------------

SKILL_LABEL_PATTERN = re.compile(
    r"^(Languages|Frameworks/Libraries|Systems/Platforms|Tools/Testing)\s*:\s*(.+)$",
    re.IGNORECASE,
)
DEGREE_PATTERN = re.compile(
    r"\b(?:Bachelor|Master|B\.S\.|M\.S\.|B\.A\.|M\.A\.|Ph\.D\.?|Associate)\b", re.IGNORECASE
)
SCHOOL_PATTERN = re.compile(r"\b(?:University|College|Institute|Polytechnic)\b", re.IGNORECASE)

# -- structural validation ---------------------------------------------

FRAGMENT_START_PATTERN = re.compile(
    r"^(and|but|or|so|which|who|whom|that|while|because|since|although|"
    r"though|before|after|when|if|unless|managing|handling|resulting|"
    r"leading|including|using|involving|allowing|enabling|for|with|to|"
    r"of|in|on|by|from)\b",
    re.IGNORECASE,
)
BARE_DATE_RANGE_PATTERN = re.compile(
    r"^(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{1,2}/\d{4})\s*-\s*"
    r"(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{1,2}/\d{4}|Present|Current)\.?$",
    re.IGNORECASE,
)
BARE_CITY_STATE_PATTERN = re.compile(r"^[A-Z][A-Za-z.\s]+,\s*[A-Z]{2}\.?$")


def _json_object_text(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return text
    return text[start : end + 1]


def _entity_prefix(name: str, used: set[str]) -> str:
    """Derive an <ENTITY> id prefix from a company or project name.

    Prefers an acronym-like token already in the name ("NASA California
    Space Grant Consortium" -> NASA); otherwise takes initials of the
    significant words ("General Atomics" -> GA). A single word splits on its
    CamelCase seams when each part is a real word ("ThreatSense" -> TS) and
    is otherwise truncated whole ("TermIt" -> TERMIT, "Emend" -> EMEND).
    Numeric suffix on collision within the same master resume ("GA" -> "GA2").
    """
    words = [w for w in ENTITY_WORD_PATTERN.findall(name) if w.lower() not in ENTITY_STOP_WORDS]
    if not words:
        words = ENTITY_WORD_PATTERN.findall(name) or ["X"]

    acronym = next((w for w in words if w.isupper() and 2 <= len(w) <= 5), None)
    if len(words) == 1 and not acronym:
        parts = CAMEL_PART_PATTERN.findall(words[0])
        if len(parts) > 1 and all(len(p) >= MIN_CAMEL_PART for p in parts):
            words = parts

    if acronym:
        base = acronym
    elif len(words) == 1:
        base = words[0].upper()[:MAX_PREFIX_LEN]
    else:
        base = "".join(w[0] for w in words).upper()[:MAX_PREFIX_LEN]
    if len(base) < 2:
        base = (base + "XX")[:2]

    prefix = base
    suffix = 2
    while prefix in used:
        prefix = f"{base}{suffix}"
        suffix += 1
    used.add(prefix)
    return prefix


def _insert_section_breaks(text: str) -> str:
    """Isolate a recognized bare section header into its own block.

    Resumes copy-pasted from a PDF often lose the blank lines between
    sections, collapsing "Education" and "Experience" into one block. A
    known header (on its own line) is a strong enough signal to split on
    even without one -- on *both* sides, so the header word itself doesn't
    later get soft-wrap-joined into the entry content that follows it.
    """
    lines = text.splitlines()
    out: list[str] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        is_header = bool(SECTION_HEADER_PATTERN.match(stripped))
        if is_header and index > 0 and out and out[-1].strip():
            out.append("")
        out.append(line)
        if is_header and index + 1 < len(lines) and lines[index + 1].strip():
            out.append("")
    return "\n".join(out)


def _split_sentences(text: str) -> list[str]:
    """One complete sentence per fact, never a line-wrap fragment."""
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in SENTENCE_SPLIT_PATTERN.split(text) if s.strip()]


def _split_date_range(line: str) -> tuple[str, str, str]:
    """Strip a date range from `line`, returning (remaining_text, start, end)."""
    match = DATE_RANGE_PATTERN.search(line)
    if not match:
        return line.strip(), "", ""
    remaining = line[: match.start()] + line[match.end() :]
    remaining = re.sub(r"[(\[]\s*[)\]]", "", remaining).strip(" ,-")
    start, end = re.split(r"\s*-\s*", match.group("range"), maxsplit=1)
    return remaining, start.strip(), end.strip()


def _split_location(line: str) -> tuple[str, str]:
    """Strip a trailing "City, ST"-shaped location, returning (remaining, location).

    "<org> <city>, ST" is genuinely ambiguous without a gazetteer: in
    "Riverside State University Riverside, CA" the two-word city reading
    swallows part of the school name. A comma separating org from city
    settles it outright; without one, prefer the longest reading that leaves
    neither a dangling connector nor an org noun stranded in the city.
    """
    comma_match = COMMA_LOCATION_PATTERN.match(line.strip())
    if comma_match:
        head, location = comma_match.group("head").strip(), comma_match.group("loc")
        city, _, state = location.rpartition(",")
        words = city.split()
        # "University of California, Riverside Riverside, CA": a city never
        # repeats its own name, so the first copy is the tail of the org's
        # name and belongs back on the head
        if len(words) == 2 and words[0].lower() == words[1].lower():
            return f"{head}, {words[0]}", f"{words[1]},{state}"
        return head, location

    candidates = [
        (line[: match.start(1)].strip(), match.group(1))
        for pattern in LOCATION_SUFFIX_PATTERNS
        if (match := pattern.search(line))
    ]
    if not candidates:
        return line.strip(), ""
    remaining, location = next(
        (
            c
            for c in candidates
            if not DANGLING_TAIL_PATTERN.search(c[0])
            and c[1].split()[0].lower() not in ORG_TAIL_WORDS
        ),
        candidates[0],
    )
    return remaining.strip(" ,@&/-"), location


def _split_grad_date(line: str) -> tuple[str, str]:
    """Strip a trailing (possibly "Expected"-prefixed) graduation date."""
    match = GRAD_DATE_PATTERN.search(line)
    if not match:
        return line.strip(), ""
    return line[: match.start()].strip(" ,.-"), match.group(0).strip()


def _split_tech(text: str) -> tuple[str, list[str]]:
    """A project header's "Name | tech, tech" shape, if present."""
    if "|" not in text:
        return text.strip(), []
    name, tech_text = text.split("|", 1)
    return name.strip(), [t.strip() for t in tech_text.split(",") if t.strip()]


def _section_kind(header_line: str) -> str | None:
    """Which MasterResume list a recognized bare section header routes to."""
    stripped = header_line.strip().rstrip(":")
    if re.fullmatch(r"educations?", stripped, re.IGNORECASE):
        return "education"
    if re.fullmatch(r"projects?", stripped, re.IGNORECASE):
        return "project"
    if re.fullmatch(r"(?:work |professional |relevant )?experiences?", stripped, re.IGNORECASE):
        return "experience"
    if re.fullmatch(r"(?:technical |core )?skills?", stripped, re.IGNORECASE):
        return "skills"
    if SECTION_HEADER_PATTERN.match(stripped):
        return "skip"
    return None


def _looks_like_education_block(lines: list[str]) -> bool:
    """Infer an education entry from a degree phrase plus a school name.

    Lets education parse correctly even without an explicit "Education"
    header -- some resumes fold it into a "Leadership" or unheaded block.
    """
    text = " ".join(lines)
    return bool(DEGREE_PATTERN.search(text) and SCHOOL_PATTERN.search(text))


def _merge_skill_line(skills: dict[str, list[str]], line: str) -> None:
    """Route a "Label: a, b, c" (or bare "a, b, c") line into the skills dict."""
    match = SKILL_LABEL_PATTERN.match(line)
    label, items_text = (match.group(1), match.group(2)) if match else ("Skills", line)
    items = [item.strip().rstrip(".") for item in items_text.split(",") if item.strip()]
    if not items:
        return
    bucket = skills.setdefault(label, [])
    bucket.extend(item for item in items if item not in bucket)


def _pull_labeled_lines(
    lines: list[str], skills: dict[str, list[str]]
) -> tuple[list[str], list[str]]:
    """Drain "Coursework:"/skill-category lines out of a block's content.

    A "Label: a, b, c" line is structure -- it belongs in `skills` or an
    education entry's coursework, and must never be minted as a fact.
    Returns the remaining content lines and the coursework it pulled out.
    """
    remaining: list[str] = []
    coursework: list[str] = []
    for line in lines:
        course = COURSEWORK_PATTERN.match(line)
        if course:
            coursework.extend(
                c.strip().rstrip(".") for c in course.group(1).split(",") if c.strip()
            )
            continue
        if SKILL_LABEL_PATTERN.match(line):
            _merge_skill_line(skills, line)
            continue
        remaining.append(line)
    return remaining, coursework


def _looks_like_fact_line(line: str) -> bool:
    # checked on raw, pre-unwrap lines, so recognize any bullet glyph
    # unwrap_text would later normalize -- not just the plain-ASCII ones
    return bool(BULLET_START_PATTERN.match(line)) or line.rstrip()[-1:] in (".", "!", "?")


def _has_date(line: str) -> bool:
    return bool(DATE_RANGE_PATTERN.search(line) or BARE_YEAR_PATTERN.search(line))


def _is_entry_boundary(lines: list[str], index: int, kind: str) -> bool:
    """Whether `lines[index]` starts a new experience/project entry.

    Jake's-style header is two lines -- title + dates, then org + location --
    and the date can sit on either of them. A dated non-bullet line starts an
    entry outright; a dateless one does too when the very next non-bullet
    line carries the date, which is what makes "Technical Lead" / "ACM @ UCR
    Riverside, CA 2025" one entry rather than trailing content of the last.
    Projects often carry no date at all, so a "Name | tech, tech" header --
    the other line a fact must never be minted from -- serves there instead.
    """
    line = lines[index]
    if _looks_like_fact_line(line):
        return False
    if DATE_RANGE_PATTERN.search(line):
        return True
    if kind == "project" and "|" in line:
        return True
    following = lines[index + 1] if index + 1 < len(lines) else ""
    return bool(following) and not _looks_like_fact_line(following) and _has_date(following)


def _split_entries(lines: list[str], kind: str) -> list[list[str]]:
    """Split a section's lines into per-entry groups at header boundaries.

    Blank-line block splitting alone can't segment entries that run
    together without blank lines between them -- this is the fix for
    entries collapsing into one when a resume omits those blank lines.
    """
    entries: list[list[str]] = []
    current: list[str] = []
    for index, line in enumerate(lines):
        if current and _is_entry_boundary(lines, index, kind):
            entries.append(current)
            current = []
        current.append(line)
    if current:
        entries.append(current)
    return entries


def _parse_entry_header(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """Split an entry's lines into (metadata, remaining fact lines).

    Jake's-template shape is usually two lines (company + location, title +
    dates, in either order), but title/company/dates sometimes each get
    their own line -- keep consuming header lines up to a bound, so long as
    they don't look like fact content yet.
    """
    header: list[str] = []
    idx = 0
    while idx < len(lines) and idx < 4 and not _looks_like_fact_line(lines[idx]):
        header.append(lines[idx])
        idx += 1

    # Signal priority, not line order: a date on a line makes it a title
    # candidate, a location makes it a company candidate. Only a line with
    # neither signal falls back to filling whatever field is still empty --
    # otherwise an unsignaled line (e.g. a bare title) could claim "company"
    # before a later, better-signaled line (the actual company + location)
    # ever gets a chance to.
    start = end = location = ""
    dated: list[str] = []
    located: list[str] = []
    plain: list[str] = []
    for line in header:
        # a lone trailing year (no real range) is common on club/project
        # headers -- strip it before location splitting so it can't stick to
        # a location suffix ("Riverside, CA 2025") and break that match
        bare_year = ""
        year_match = BARE_YEAR_PATTERN.search(line)
        if year_match and not DATE_RANGE_PATTERN.search(line):
            bare_year = year_match.group(1)
            line = line[: year_match.start()].rstrip(" ,-")
        text, s, e = _split_date_range(line)
        if s or e:
            start, end = start or s, end or e
            text, loc = _split_location(text)
            location = location or loc
            dated.append(text)
            continue
        text, loc = _split_location(line)
        if loc:
            location = location or loc
            located.append(text)
        else:
            plain.append(text)
        end = end or bare_year

    title = " ".join(t for t in dated if t)
    company = " ".join(t for t in located if t)
    if not title and plain:
        title = plain.pop(0)
    if not company and plain:
        company = plain.pop(0)
    if not company and not title:
        company = header[0] if header else ""
    if not company:
        company = title
    if not title:
        title = company

    return (
        {"company": company, "title": title, "location": location, "start": start, "end": end},
        lines[idx:],
    )


def _parse_education_entry(lines: list[str]) -> Education:
    """Parse an education entry line by line, never as one joined blob.

    Jake's-style shape is two lines -- school (+ trailing "City, ST") then
    degree (+ trailing graduation date) -- but the order varies and either
    half may share a line, so each line is classified by the signals it
    carries rather than by its position. Education entries hold no facts:
    anything left over after school/degree/location/date is dropped.
    """
    school = degree = location = grad_date = ""
    coursework: list[str] = []
    leftovers: list[str] = []
    for line in lines:
        course = COURSEWORK_PATTERN.match(line)
        if course:
            coursework.extend(
                c.strip().rstrip(".") for c in course.group(1).split(",") if c.strip()
            )
            continue
        text, date = _split_grad_date(line)
        grad_date = grad_date or date
        text, loc = _split_location(text)
        location = location or loc
        # a one-liner packs both halves in: "<School> - <Degree>"
        text, _, tail = (t.strip() for t in text.partition(" - "))
        for part in (text, tail):
            part = part.strip(" ,.-")
            if not part:
                continue
            if DEGREE_PATTERN.search(part) and not degree:
                degree = part
            elif not school:
                school = part
            else:
                leftovers.append(part)
    if not school and leftovers:
        school = leftovers[0]
    return Education(
        school=school, degree=degree, location=location, grad_date=grad_date, coursework=coursework
    )


def _extract_name(first_line: str) -> str:
    """The name portion of a header line, cut off before any contact info."""
    matches = [
        m
        for m in (
            EMAIL_PATTERN.search(first_line),
            PHONE_PATTERN.search(first_line),
            LINK_PATTERN.search(first_line),
        )
        if m
    ]
    candidate = first_line[: min(m.start() for m in matches)] if matches else first_line
    candidate = re.split(r"\s*[|•·]\s*", candidate)[0].strip()
    return candidate or "Unknown"


def _text_master_resume(text: str) -> MasterResume:
    """Deterministic fallback: turn pasted plain text into a fact schema.

    Not as capable as the real LLM path, but sentence-aware (one fact is one
    complete sentence), separates entry metadata from facts, and routes
    education correctly -- stable and valid without an API key.
    """
    lines = [line.strip() for line in text.splitlines()]
    name = _extract_name(next((line for line in lines if line), ""))
    email = match.group(0) if (match := EMAIL_PATTERN.search(text)) else ""
    phone = match.group(0).strip() if (match := PHONE_PATTERN.search(text)) else ""
    links = list(dict.fromkeys(link.rstrip(".,;|") for link in LINK_PATTERN.findall(text)))

    contact_lines = {name}
    experiences: list[Experience] = []
    projects: list[Project] = []
    education: list[Education] = []
    skills: dict[str, list[str]] = {}
    coursework: list[str] = []
    used_ids: set[str] = set()
    current_kind = "experience"

    for block in re.split(r"\n\s*\n", text.strip()):
        block_lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not block_lines:
            continue
        kind = _section_kind(block_lines[0])
        if kind is not None:
            current_kind = kind
            block_lines = block_lines[1:]
        if not block_lines or current_kind == "skip":
            continue
        block_lines = [
            line
            for line in block_lines
            if line not in contact_lines and not EMAIL_PATTERN.search(line)
        ]
        if current_kind == "skills":
            for line in block_lines:
                _merge_skill_line(skills, line)
            continue
        # labeled lines are structure, never fact content
        block_lines, block_coursework = _pull_labeled_lines(block_lines, skills)
        coursework.extend(block_coursework)
        if not block_lines:
            continue

        # an explicit header wins, but a degree phrase plus a school name is
        # enough on its own -- some resumes never write "Education" at all
        if current_kind == "education" or _looks_like_education_block(block_lines):
            education.append(_parse_education_entry(block_lines))
            continue

        for entry_lines in _split_entries(block_lines, current_kind):
            meta, fact_lines = _parse_entry_header(entry_lines)
            # unwrap only the fact content: rejoins genuinely wrapped sentences
            # without risking header lines (no terminal punctuation of their
            # own) being soft-wrap-joined into it first
            unwrapped_facts = unwrap_text("\n".join(fact_lines)) if fact_lines else ""
            facts_text: list[str] = []
            for line in unwrapped_facts.splitlines():
                facts_text.extend(_split_sentences(BULLET_PATTERN.sub("", line)))
            facts_text = facts_text[:MAX_FACTS_PER_SECTION]
            if not facts_text:
                continue

            if current_kind == "project":
                proj_name, tech = _split_tech(meta["company"])
                section_id = _entity_prefix(proj_name, used_ids)
                projects.append(
                    Project(
                        id=section_id,
                        name=proj_name,
                        tech=tech,
                        facts=[
                            Fact(id=f"{section_id}-{i:02d}", text=t)
                            for i, t in enumerate(facts_text, 1)
                        ],
                    )
                )
            else:
                section_id = _entity_prefix(meta["company"], used_ids)
                experiences.append(
                    Experience(
                        id=section_id,
                        company=meta["company"],
                        title=meta["title"],
                        location=meta["location"],
                        start=meta["start"],
                        end=meta["end"],
                        facts=[
                            Fact(id=f"{section_id}-{i:02d}", text=t)
                            for i, t in enumerate(facts_text, 1)
                        ],
                    )
                )

    if coursework and education:
        merged = education[0].coursework + [
            c for c in coursework if c not in education[0].coursework
        ]
        education[0] = education[0].model_copy(update={"coursework": merged})

    return MasterResume(
        name=name,
        email=email,
        phone=phone,
        links=links,
        education=education,
        experiences=experiences,
        projects=projects,
        skills=skills,
    )


def _fact_violations(fact_text: str, company: str, title: str) -> list[str]:
    """Why a fact isn't a clean, complete, on-topic sentence, if it isn't."""
    reasons = []
    stripped = fact_text.strip()
    if not stripped:
        return ["empty fact"]
    if stripped[-1] not in ".!?":
        reasons.append("does not end in . ! or ?")
    if stripped[0].islower() or FRAGMENT_START_PATTERN.match(stripped):
        reasons.append("starts lowercase or with a fragment continuation")
    if BARE_DATE_RANGE_PATTERN.match(stripped):
        reasons.append("is a bare date range, not a fact")
    if BARE_CITY_STATE_PATTERN.match(stripped):
        reasons.append("is a bare city/state, not a fact")
    norm = stripped.lower().rstrip(".!?")
    if company and norm == company.strip().lower():
        reasons.append("restates the entry's company")
    if title and norm == title.strip().lower():
        reasons.append("restates the entry's title")
    return reasons


def _validate_structure(master: MasterResume) -> list[str]:
    """Every violation across every fact, as `"<fact id>: <reasons>"` strings."""
    violations: list[str] = []
    for entry in [*master.experiences, *master.projects]:
        company = getattr(entry, "company", "") or getattr(entry, "name", "")
        title = getattr(entry, "title", "")
        for fact in entry.facts:
            reasons = _fact_violations(fact.text, company, title)
            if reasons:
                violations.append(f"{fact.id} ({fact.text!r}): {'; '.join(reasons)}")
    return violations


class _RawFact(BaseModel):
    text: str


class _RawExperience(BaseModel):
    company: str
    title: str
    location: str
    start: str
    end: str
    facts: list[_RawFact]


class _RawProject(BaseModel):
    name: str
    tech: list[str]
    facts: list[_RawFact]


class _RawMasterResume(BaseModel):
    """What the LLM returns: no ids anywhere -- Python assigns those after."""

    name: str
    email: str
    phone: str
    links: list[str]
    education: list[Education]
    experiences: list[_RawExperience]
    projects: list[_RawProject]
    skills: dict[str, list[str]]


def _assign_ids(raw: _RawMasterResume) -> MasterResume:
    """Turn LLM output with no ids into a MasterResume with entity-derived ones."""
    used_ids: set[str] = set()
    experiences = []
    for exp in raw.experiences:
        section_id = _entity_prefix(exp.company, used_ids)
        experiences.append(
            Experience(
                id=section_id,
                company=exp.company,
                title=exp.title,
                location=exp.location,
                start=exp.start,
                end=exp.end,
                facts=[
                    Fact(id=f"{section_id}-{i:02d}", text=f.text)
                    for i, f in enumerate(exp.facts, 1)
                ],
            )
        )
    projects = []
    for proj in raw.projects:
        section_id = _entity_prefix(proj.name, used_ids)
        projects.append(
            Project(
                id=section_id,
                name=proj.name,
                tech=proj.tech,
                facts=[
                    Fact(id=f"{section_id}-{i:02d}", text=f.text)
                    for i, f in enumerate(proj.facts, 1)
                ],
            )
        )
    return MasterResume(
        name=raw.name,
        email=raw.email,
        phone=raw.phone,
        links=raw.links,
        education=raw.education,
        experiences=experiences,
        projects=projects,
        skills=raw.skills,
    )


def _mock_structure_resume(text: str) -> MasterResume:
    """Mock structuring: MasterResume JSON fast path, plain-text fallback."""
    json_text = _json_object_text(text)
    looks_like_json = "```json" in text.lower() or text.strip().startswith("{")
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        if looks_like_json:
            raise ValueError("MOCK structure_resume found invalid MasterResume JSON") from exc
        return _validated_text_master_resume(text)
    try:
        return MasterResume(**data)
    except ValidationError:
        if looks_like_json:
            raise
        # incidental braces inside prose, not a schema payload
        return _validated_text_master_resume(text)


def _validated_text_master_resume(text: str) -> MasterResume:
    """The text-parsing path only -- pre-structured JSON is trusted as-is.

    unwrap_text is deliberately NOT run over the whole block here: header
    lines (title, company, dates) rarely end in terminal punctuation, so a
    global unwrap would soft-wrap-join them straight into the fact content
    that follows. Bullets are a reliable header/fact boundary regardless of
    wrapping, so headers are found on the raw lines first, and only the
    remaining fact lines get unwrapped -- see `_text_master_resume`.
    """
    # order matters: break runaway "header • first bullet" lines apart first
    # so a header is a header before dates get reattached to one, and only
    # then isolate section headers into their own blocks
    text = split_inline_bullets(text)
    text = reattach_orphan_dates(text)
    text = _insert_section_breaks(text)
    master = _text_master_resume(text)
    violations = _validate_structure(master)
    if violations:
        raise ValueError("structure_resume produced invalid facts: " + "; ".join(violations))
    return master


def _check_input_size(text: str, label: str) -> None:
    limit = max_input_chars()
    if len(text) > limit:
        raise ValueError(f"{label} exceeds {limit} characters")


def _real_structure_resume(text: str, *, client: Any | None = None) -> MasterResume:
    """Structure with the LLM, repairing once against structural violations."""
    prompt = f"Resume text:\n\n{text}"
    violations: list[str] = []
    for _attempt in range(2):
        if violations:
            prompt += (
                "\n\nYour previous response produced invalid facts:\n"
                + "\n".join(violations)
                + "\nFix these specific facts and return a corrected structure."
            )
        result = structured_call_with_usage(
            FAST_MODEL,
            cacheable_system(STRUCTURE_SYSTEM),
            prompt,
            _RawMasterResume,
            client=client,
        )
        record_call(
            label="structure_resume",
            model=FAST_MODEL,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cache_read_input_tokens=result.cache_read_input_tokens,
            cache_creation_input_tokens=result.cache_creation_input_tokens,
        )
        master = _assign_ids(result.value)
        violations = _validate_structure(master)
        if not violations:
            return master
    raise ValueError(
        "structure_resume produced invalid facts after repair retry: " + "; ".join(violations)
    )


def structure_resume(text: str, *, client: Any | None = None) -> MasterResume:
    """Turn pasted resume text into a confirmed-fact schema."""
    _check_input_size(text, "resume text")
    if mock_enabled():
        return _mock_structure_resume(text)
    return _real_structure_resume(unwrap_text(text), client=client)


def parse_jd(text: str, *, client: Any | None = None) -> JDExtract:
    """Extract structure from a job posting."""
    _check_input_size(text, "job posting text")
    if not mock_enabled():
        result = structured_call_with_usage(
            FAST_MODEL,
            cacheable_system(PARSE_JD_SYSTEM),
            f"Job posting:\n\n{text}",
            JDExtract,
            client=client,
        )
        record_call(
            label="parse_jd",
            model=FAST_MODEL,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cache_read_input_tokens=result.cache_read_input_tokens,
            cache_creation_input_tokens=result.cache_creation_input_tokens,
        )
        return result.value
    json_text = _json_object_text(text)
    is_json_hint = "```json" in text.lower()
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        if is_json_hint or json_text != text:
            raise ValueError("MOCK parse_jd found invalid JDExtract JSON") from exc
        keywords = [
            token
            for token in dict.fromkeys(JD_TOKEN_PATTERN.findall(text))
            if token.lower() not in JD_STOP_WORDS
        ]
        return JDExtract(
            company="",
            title="",
            hard_skills=[],
            soft_requirements=[],
            responsibilities=[text.strip()] if text.strip() else [],
            keywords=keywords,
        )
    return JDExtract(**data)


def _fact_bullets(facts) -> list[TailoredBullet]:
    return [TailoredBullet(text=fact.text, source_fact_ids=[fact.id]) for fact in facts]


def experience_section(experience: Experience) -> TailoredSection:
    """Convert confirmed experience facts into grounded bullets."""
    return TailoredSection(
        ref_id=experience.id, bullets=_fact_bullets(experience.facts)
    )


def project_section(project: Project) -> TailoredSection:
    """Convert confirmed project facts into grounded bullets."""
    return TailoredSection(ref_id=project.id, bullets=_fact_bullets(project.facts))


def mock_refactor_resume(master: MasterResume) -> TailoredResume:
    """Return a renderable resume using only confirmed master facts.

    Used by `refactor` in both modes: the no-JD path is a pass-through of
    already-confirmed facts, so there is nothing for an LLM to add.
    """
    return TailoredResume(
        summary_of_strategy="Mock refactor: preserve confirmed facts without rewriting.",
        experiences=[
            experience_section(experience) for experience in master.experiences
        ],
        projects=[project_section(project) for project in master.projects],
        skills=master.skills,
    )


def mock_refactor_result(master: MasterResume) -> tuple[TailoredResume, Report]:
    """Return grounded mock refactor output plus its validation report."""
    tailored = mock_refactor_resume(master)
    validate_grounding(master, tailored)
    return tailored, build_grounding_report(tailored, 0.0, [], [])


def refactor(master: MasterResume) -> TailoredResume:
    """Public refactor entrypoint; MOCK mode preserves confirmed facts."""
    tailored, _report = mock_refactor_result(master)
    return tailored


def mock_tailor_resume(
    master: MasterResume, jd: JDExtract
) -> tuple[TailoredResume, Report]:
    """Return grounded mock tailoring plus its validation report."""
    tailored = mock_refactor_resume(master)
    score, matched, missing = keyword_match(jd, master)
    tailored.summary_of_strategy = (
        "Mock tailor: preserve facts and report keyword overlap."
    )
    validate_grounding(master, tailored)
    return tailored, build_grounding_report(tailored, score, matched, missing)


def _tailor_user_prompt(jd: JDExtract) -> str:
    return (
        "Tailor the confirmed master resume in the system prompt to this "
        f"posting:\n\n{jd.model_dump_json(indent=2)}"
    )


def real_tailor_resume(
    master: MasterResume, jd: JDExtract, *, client: Any | None = None
) -> TailoredResume:
    """Tailor with Sonnet, then reject anything the validator will not accept.

    The master resume rides in the cached system block so repeated tailoring
    for one session reuses the prefix.
    """
    result = structured_call_with_usage(
        TAILOR_MODEL,
        cacheable_system(TAILOR_SYSTEM, f"Confirmed master resume:\n{master.model_dump_json()}"),
        _tailor_user_prompt(jd),
        TailoredResume,
        client=client,
    )
    record_call(
        label="tailor",
        model=TAILOR_MODEL,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cache_read_input_tokens=result.cache_read_input_tokens,
        cache_creation_input_tokens=result.cache_creation_input_tokens,
    )
    tailored = result.value
    # Unvalidated output must never leave the pipeline.
    validate_grounding(master, tailored)
    return tailored


def real_tailor_result(
    master: MasterResume, jd: JDExtract, *, client: Any | None = None
) -> tuple[TailoredResume, Report]:
    """Return real tailored output plus its two-stage validation report."""
    tailored = real_tailor_resume(master, jd, client=client)
    score, matched, missing = keyword_match(jd, master)
    verdicts = judge_bullets(master, tailored, client=client)
    report = build_grounding_report(tailored, score, matched, missing)
    report.verdicts = verdicts
    report.grounding_ok = all(verdict.supported for verdict in verdicts)
    return tailored, report


def tailor(
    master: MasterResume, jd: JDExtract, *, client: Any | None = None
) -> TailoredResume:
    """Public tailor entrypoint; MOCK mode preserves confirmed facts."""
    if mock_enabled():
        tailored, _report = mock_tailor_resume(master, jd)
        return tailored
    return real_tailor_resume(master, jd, client=client)
