"""Deterministic keyword matching for job descriptions.

Keywords are pulled straight out of the posting's own text via a few
literal, non-ML heuristics below -- never asked of an LLM (unpinned, it
answers differently call to call for the same text, which made the score
visibly change across identical re-submissions) and never gated behind a
fixed dictionary (which caps coverage at whatever someone thought to add
ahead of time, and misses ordinary phrases like "cross-functional
collaboration" that never make anyone's tech-skills list).

The tradeoff every keyword tool built this way runs into: a phrase only
counts if the posting states it as its own short, literal unit -- a bullet
line, an item in a comma-separated list after a lead-in like "experience
with", or a Capitalized proper-noun-looking phrase. We do not paraphrase,
normalize, or infer a requirement the posting doesn't literally state,
because that's exactly the class of bug where a keyword "clearly in the
resume" still gets flagged as missing -- the extraction and the matching
stop agreeing on what the phrase actually looked like.
"""

import re

from core.schemas import JDExtract, MasterResume

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

MAX_PHRASE_WORDS = 5
MAX_KEYWORDS = 30

# Words too generic to ever stand alone as a keyword, and too common as
# sentence-starters for the proper-noun heuristic below to trust on their own.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "be", "as", "at", "by", "from", "this", "that", "our",
    "we", "you", "your", "will", "who", "role", "team", "job", "work",
    "about", "overview", "responsibilities", "requirements", "qualifications",
    "why", "what", "us", "here", "join", "every", "each", "any", "all",
    "it", "its", "i", "experience", "experienced", "familiarity", "familiar",
    "proficiency", "proficient", "expertise", "expert", "background",
    "knowledge", "knowledgeable", "skill", "skills", "skilled", "adept",
    "competent", "capable",
    "strong", "contribute", "company", "polished", "united", "states",
    "usd", "u.s", "annual", "professional", "training", "location",
    "business", "needs", "demand", "market", "career", "id",
}

# A JD flattened to one line (see core/jd_text.py) still has real sentences
# in it -- "...open Monday through Friday" reads as a Capitalized run
# indistinguishable from a real term unless day/month names are excluded
# outright. These are never a keyword on their own merits, so any phrase
# containing one is dropped regardless of position.
_CALENDAR_WORDS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "january", "february", "march", "april", "june", "july",
    "august", "september", "october", "november", "december",
}

# Boilerplate section headers a flattened JD page runs straight into the
# next sentence with no punctuation between them (html_to_jd_text collapses
# block-level breaks to a single space) -- without this, "Role Summary The
# Software..." reads as one Capitalized run. Checked against a phrase's
# first word only, so it doesn't also swallow a real term like "Team
# Foundation Server" that happens to contain one of these words later on.
_SECTION_HEADING_STARTS = {
    "role", "summary", "overview", "about", "responsibilities",
    "qualifications", "requirements", "benefits", "rewards", "total",
    "equal", "opportunity", "compensation", "perks",
}

# "Requirements: Python, Docker, strong communication skills" -- a lead-in
# phrase followed by a list is one of the most reliable structural signals
# a posting gives for "these specifically are the keywords."
_LIST_LEAD_IN = re.compile(
    r"(?:experience|proficiency|expertise|background)\s+(?:with|in)|"
    r"knowledge\s+of|familiarity\s+with|skills?\s*(?:in|with)?\s*:|"
    r"requirements?\s*:|qualifications?\s*:|preferred\s+qualifications?\s*:|"
    r"you\s+(?:have|will|are|bring|need)\s*:|"
    r"what\s+you(?:'ll|\s+will)\s+(?:do|need|bring)\s*:|"
    r"nice\s+to\s+have\s*:|must\s+have\s*:|such\s+as",
    re.IGNORECASE,
)

_LIST_SPLIT = re.compile(r",|/|\band\b|\bor\b", re.IGNORECASE)

# Trailing/leading filler that commonly rides along a listed skill
# ("Docker required", "strongly preferred: Python") but isn't part of it.
_FILLER_EDGES = {
    "required", "preferred", "needed", "necessary", "mandatory", "strongly",
    "ideally", "must", "plus",
}

# A run of Capitalized Words -- catches named technologies/products
# ("Node.js", "Google Cloud Platform") wherever they appear in prose,
# without needing a lead-in phrase at all. A period only continues the
# match when followed by more of a word (so "Node.js" stays one token but
# a sentence-final "Python." doesn't drag its period along). The connector
# is horizontal whitespace only -- plain \s+ crosses newlines, which would
# fuse three separate bullet items ("Python\nDocker\nStrong") into one fake
# multi-word phrase.
_PROPER_NOUN = re.compile(
    r"\b[A-Z][A-Za-z0-9+#]*(?:\.[A-Za-z0-9+#]+)*"
    r"(?:[ \t]+[A-Z][A-Za-z0-9+#]*(?:\.[A-Za-z0-9+#]+)*){0,2}\b"
)
# A fresh bullet marker ("- Analyze...") or a colon introducing a clause
# ("About Acme: Founded in 2005...") is just as much a boundary as a period
# or newline -- without these, the bullet's own leading verb or the word
# right after the colon reads as "mid-sentence" and survives as noise.
_SENTENCE_BOUNDARY = re.compile(r"[.!?\n:]\s*$|[•\-*·]\s*$")

# A career-page header's "City, ST" (e.g. "San Mateo, CA") reads as two
# separate Capitalized runs once split on the comma -- neither the city
# name nor the bare state code is ever a job-posting keyword.
_FOLLOWED_BY_STATE_CODE = re.compile(r"^,\s*[A-Z]{2}(?:\s|[,.:]|$)")
_PRECEDED_BY_COMMA = re.compile(r",\s*$")


def _clean_phrase(phrase: str) -> str:
    return phrase.strip(" \t.,;:-•").strip()


def _trim_filler(phrase: str) -> str:
    words = phrase.split()
    while words and words[-1].lower().strip(".,") in _FILLER_EDGES:
        words.pop()
    while words and words[0].lower().strip(".,") in _FILLER_EDGES:
        words.pop(0)
    return " ".join(words)


def _is_plausible_keyword(phrase: str) -> bool:
    words = phrase.split()
    if not words or len(words) > MAX_PHRASE_WORDS:
        return False
    return not all(w.lower().strip(".,") in _STOPWORDS for w in words)


def _candidate(raw_item: str) -> str | None:
    phrase = _trim_filler(_clean_phrase(raw_item))
    return phrase if _is_plausible_keyword(phrase) else None


def _phrases_from_lead_in_lists(text: str) -> list[str]:
    found = []
    for match in _LIST_LEAD_IN.finditer(text):
        window = text[match.end() : match.end() + 120]
        # stop at the first sentence end OR line break -- a cue phrase
        # immediately followed by its own newline-separated bullet list
        # (handled by _phrases_from_short_lines instead) must not bleed
        # into whatever comes after those newlines.
        boundary = re.search(r"[.\n]", window)
        tail = window[: boundary.start()] if boundary else window
        items = _LIST_SPLIT.split(tail)
        if boundary is None and items:
            # the window ended at the 120-char cutoff, not a real sentence
            # boundary -- the last split item is likely a word chopped mid-way
            # ("...one or more langu[age]s") rather than a genuine list item
            items = items[:-1]
        for item in items:
            candidate = _candidate(item)
            # a genuine list item is short; anything longer without ever
            # hitting a comma/and/or is more likely a prose continuation
            # than a keyword ("an interest in building practical" vs "Python")
            if candidate and len(candidate.split()) <= 4:
                found.append(candidate)
    return found


_MAX_LINE_CHARS = 100


def _phrases_from_short_lines(text: str) -> list[str]:
    """A pasted JD's own line breaks usually survive (a URL fetch's don't --
    see core/jd_text.py's flattening, which joins every block into one
    line) -- a short line with no sentence-ending punctuation is almost
    always its own bulleted requirement.

    The length cap matters more than it looks: text with zero newlines at
    all is exactly ONE "line" per splitlines(), so without it, a whole
    multi-thousand-character flattened page that simply doesn't happen to
    end in a period would get treated as one giant bullet and shredded on
    every comma/and/or in the entire document.
    """
    found = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or len(stripped) > _MAX_LINE_CHARS:
            continue
        if stripped.endswith((".", "!", "?", ":")):
            continue
        for item in _LIST_SPLIT.split(stripped):
            candidate = _candidate(item)
            if candidate:
                found.append(candidate)
    return found


def _proper_noun_phrases(text: str) -> list[str]:
    found = []
    for match in _PROPER_NOUN.finditer(text):
        phrase = match.group(0)
        if len(phrase) <= 1:
            continue
        words = phrase.split()
        # a Capitalized run that opens with a pronoun/article/quantifier
        # ("You Have", "Every", "The") is a sentence fragment that only
        # looks like a proper noun because it happens to sit mid-sentence
        # in flattened text -- no real skill or product name starts this way
        if words[0].lower() in _SECTION_HEADING_STARTS or words[0].lower() in _STOPWORDS:
            continue
        if any(w.lower() in _CALENDAR_WORDS for w in words):
            continue
        if _FOLLOWED_BY_STATE_CODE.match(text[match.end() : match.end() + 6]):
            continue  # "San Mateo, CA" -- this run is the city half of an address
        if (
            len(words) == 1
            and len(phrase) == 2
            and phrase.isupper()
            and _PRECEDED_BY_COMMA.search(text[: match.start()])
        ):
            continue  # the state-code half of the same address
        # a single capitalized word is ambiguous (a real term, or just a
        # sentence-starter); only trust it away from a sentence boundary --
        # a 2-3 word Capitalized run is a strong enough signal on its own
        if len(words) == 1 and _SENTENCE_BOUNDARY.search(text[: match.start()] or "."):
            continue
        found.append(phrase)
    return found


def _is_word_run(shorter: list[str], longer: list[str]) -> bool:
    """True if `shorter`'s words appear as a contiguous run inside `longer`."""
    n, m = len(shorter), len(longer)
    return n > 0 and n <= m and any(longer[i : i + n] == shorter for i in range(m - n + 1))


def _drop_redundant_superstrings(phrases: list[str]) -> list[str]:
    """Different heuristics above can surface both "cross-functional
    collaboration" and the noisier "experience with cross-functional
    collaboration" for the same posting -- keep the shorter, cleaner phrase
    (also the one more likely to appear verbatim on a resume) and drop any
    phrase that's just a wrapper around one already kept.

    Containment is checked word-by-word, not as a raw character substring --
    "Java" is not a redundant wrapper of "JavaScript", nor is "C" of "C++",
    even though the letters happen to line up."""
    word_lists = [p.lower().split() for p in phrases]
    return [
        phrase
        for i, phrase in enumerate(phrases)
        if not any(
            i != j and word_lists[j] != word_lists[i] and _is_word_run(word_lists[j], word_lists[i])
            for j in range(len(phrases))
        )
    ]


def extract_keywords(text: str) -> list[str]:
    """Candidate keyword phrases straight out of the posting's own text.
    Deterministic (the same text always yields the same list) and literal
    (every result is a real substring of `text`, first-seen order, capped
    at MAX_KEYWORDS so a long posting doesn't flood the score card)."""
    candidates = [
        *_phrases_from_lead_in_lists(text),
        *_phrases_from_short_lines(text),
        *_proper_noun_phrases(text),
    ]
    seen: set[str] = set()
    deduped: list[str] = []
    for phrase in candidates:
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(phrase)
    return _drop_redundant_superstrings(deduped)[:MAX_KEYWORDS]


_NAME_SEGMENT_SPLIT = re.compile(r",|\s[-|]\s")


def drop_known_names(keywords: list[str], *names: str) -> list[str]:
    """Neither the posting's own employer name nor its own job title is a
    skill a candidate could ever claim -- filtered out wherever a keyword
    IS the posting's own employer name or job title, or one of its natural
    comma/dash-separated segments, verbatim.

    "Software Engineer, User Frameworks" splits into "Software Engineer"
    and "User Frameworks" -- both are still just the title, not a claim.
    "Java Developer" has no such separator, so a keyword "Java" (a real,
    independently-listed requirement that happens to share a word with the
    title) is a plain substring, not a segment, and survives."""
    blocked: set[str] = set()
    for name in names:
        if not name:
            continue
        blocked.add(name.lower())
        blocked.update(s.strip().lower() for s in _NAME_SEGMENT_SPLIT.split(name) if s.strip())
    return [k for k in keywords if k.lower() not in blocked]


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def _master_units(master: MasterResume) -> list[str]:
    """Individually matchable spans of the resume: one unit per fact, per
    skill entry, and per project (its name plus its own tech list).

    A multi-word keyword must have all of its words land inside a single
    unit to count as matched -- otherwise "team", "leadership", and
    "experience" turning up in three unrelated facts would satisfy "Team
    Leadership Experience" even though the candidate never made that claim
    as one coherent bullet.

    Company, title, and coursework are deliberately excluded — a JD keyword
    matching only an employer name is not a skill the candidate claimed.
    """
    units = [fact.text for fact in master.fact_lookup().values()]
    units.extend(skill for group in master.skills.values() for skill in group)
    units.extend(
        " ".join([project.name, *project.tech]) for project in master.projects
    )
    return units


def _unique_keywords(keywords: list[str]) -> list[str]:
    return list(dict.fromkeys(keyword for keyword in keywords if keyword.strip()))


def keyword_match(
    jd: JDExtract, master: MasterResume
) -> tuple[float, list[str], list[str]]:
    """Return normalized keyword overlap without using an LLM."""
    resume_unit_tokens = [_tokens(unit) for unit in _master_units(master)]
    matched: list[str] = []
    missing: list[str] = []
    keywords = _unique_keywords(jd.keywords)
    for keyword in keywords:
        keyword_tokens = _tokens(keyword)
        if keyword_tokens and any(
            keyword_tokens <= unit_tokens for unit_tokens in resume_unit_tokens
        ):
            matched.append(keyword)
        else:
            missing.append(keyword)
    score = len(matched) / len(keywords) if keywords else 0.0
    return score, matched, missing
