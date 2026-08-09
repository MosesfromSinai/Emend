"""Deterministic keyword matching for job descriptions.

Keywords are pulled straight out of the posting's own text via a few
literal, non-ML heuristics below -- never asked of an LLM (unpinned, it
answers differently call to call for the same text, which made the score
visibly change across identical re-submissions).

Two passes: the heuristics below first find *candidate* phrases using
purely structural signals (a bullet line, an item in a comma-separated
list after a lead-in like "experience with", a Capitalized proper-noun-
looking run, a hyphen/slash compound). Then every candidate is gated
against core/tech_names.py's curated list of real languages/frameworks/
libraries/platforms/tools/named-concepts before it's allowed to survive.
That gate exists because no structural rule can tell "Docker" (a tool)
from "Monte Carlo" (a named mathematical technique) apart -- both are an
ordinary capitalized proper noun, and no rule can tell "real-time
systems" from "machine learning frameworks" apart on shape alone either.
A bare acronym-shaped token (GNC, HITL, C++) or a phrase the posting
itself acronym-defines ("High-performance computing (HPC)") bypasses the
gate, since both are reliable enough signals on their own.

We do not paraphrase, normalize, or infer a requirement the posting
doesn't literally state, because that's exactly the class of bug where a
keyword "clearly in the resume" still gets flagged as missing -- the
extraction and the matching stop agreeing on what the phrase actually
looked like. A phrase that's only partly recognized is trimmed down to
the recognized span, not kept whole and not discarded outright -- see
_known_technical_span.
"""

import re
from itertools import zip_longest

from core.schemas import JDExtract, MasterResume
from core.tech_names import ALL_TECH_NAMES

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

MAX_PHRASE_WORDS = 5
MAX_KEYWORDS = 20

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
    "today", "tomorrow", "yesterday", "currently", "now",
    # a mission-statement intro ("...enabling human life on Mars") reads as
    # a real proper noun by capitalization alone, but a planet is never a
    # skill a candidate could claim
    "mars", "moon",
}

# A phrase's head noun can be generic even when every individual word
# passes the stopword check on its own ("major refactors", "the design",
# "related techniques") -- these are the words that make a phrase read as
# narration about work, not a thing a candidate could claim as a skill.
# Never applied to single technical words already caught elsewhere (e.g.
# a real acronym); only used to veto a phrase whose *entire* remaining
# content, once real stopwords are also excluded, is one of these.
_PROCESS_NOISE = {
    "design", "redesign", "redesigns", "refactor", "refactors", "refactoring",
    "rewrite", "rewrites", "overhaul", "overhauls", "revamp", "evolution",
    "iteration", "iterations", "solution", "solutions", "approach",
    "approaches", "technique", "techniques", "methodology", "methodologies",
    "practice", "practices", "initiative", "initiatives", "leadership",
    "mentorship", "mentoring", "ownership", "collaboration", "communication",
    "teamwork", "culture", "mindset", "safety", "usability", "simplicity",
    "clarity", "quality", "excellence", "capability", "capabilities",
    "understanding", "exposure", "insight", "insights", "ability",
    "abilities", "value", "values", "impact", "outcome", "outcomes",
    "success", "efficiency", "effectiveness", "productivity",
    "professionalism", "attitude", "passion", "curiosity", "creativity",
    "flexibility", "adaptability", "accountability", "integrity",
    "environment", "opportunity", "opportunities", "growth", "level",
    "handling", "teams", "implementation", "representation", "representations",
    # generic paradigm-nouns: the *category* a real framework/library/tool
    # would belong to, never a specific one -- "computing", not "CUDA";
    # "architecture", not "microservices". Never blocks a phrase where the
    # other word is genuinely specific ("machine learning frameworks"
    # survives since "machine"/"learning" aren't noise), only one where
    # every word is this generic ("parallel computing", "scalable
    # architectures").
    "computing", "architecture", "architectures", "system", "systems",
    "infrastructure", "framework", "frameworks", "processing", "platform",
    "platforms", "hardware",
}

# A generic degree/manner modifier dressing up a noise noun shouldn't
# rescue the phrase ("Expert-level" + "implementation" is still noise).
_GENERIC_MODIFIERS = {
    "related", "straightforward", "simple", "ongoing", "major", "expert",
    "expert-level", "entry-level", "senior-level", "junior-level",
    "mid-level",
    # paradigm/quality adjectives that describe an *approach*, not a
    # nameable framework/library/language/tool -- "real-time systems" and
    # "scalable architectures" read like resume keywords but aren't
    # anything a candidate could literally list the way "React" or
    # "Docker" is; paired with a matching generic noun in _PROCESS_NOISE
    # below, the whole phrase is rejected since neither word is specific.
    "real-time", "scalable", "parallel", "distributed", "high-level",
    "low-level", "large-scale", "small-scale", "object-oriented",
    "cross-platform", "multi-platform", "high-performance",
    "performance-critical",
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
    "equal", "opportunity", "compensation", "perks", "basic", "preferred",
}

# "Requirements: Python, Docker, strong communication skills" -- a lead-in
# phrase followed by a list is one of the most reliable structural signals
# a posting gives for "these specifically are the keywords."
_LIST_LEAD_IN = re.compile(
    r"(?:experience|proficiency|expertise|background)\s+(?:with|in)|"
    r"knowledge\s+of|familiarity\s+with|skills?\s*(?:in|with)?\s*:|"
    r"requirements?\s*:|qualifications?\s*:|preferred\s+qualifications?\s*:|"
    r"what\s+you(?:'ll|\s+will)\s+(?:do|need|bring)\s*:|"
    # bare "You Will:"/"You Are:" is deliberately excluded -- on most
    # postings it introduces full-sentence bullets ("You Will: Join a
    # community of curious, supportive engineers...") whose incidental
    # commas read as a fake list ("supportive engineers", "Pursuing"), not
    # a real one. ", like X and Y" is a real list cue worth trusting
    # precisely because the comma+like combination rarely opens a plain verb
    # phrase the way bare "like" alone would ("we'd like to...").
    r",\s+like\s+|"
    r"nice\s+to\s+have\s*:|must\s+have\s*:|such\s+as|including",
    re.IGNORECASE,
)

# A colon almost never appears in JD prose except to introduce an
# elaboration or list -- catches lead-ins no fixed keyword list could
# enumerate ("...writing safe code: strong command of...", "HPC
# background:") without needing a word in front of it at all. A colon
# glued to digits ("9:00", a ratio "3:1") is a time/ratio, not a list cue.
_GENERIC_COLON = re.compile(r"(?<!\d):(?!\d)")

# A colon closing a section heading or a "You Will:"/"You Are:" bullet
# opener introduces a whole block of prose, not a literal list -- treating
# it as one shreds an ordinary sentence's incidental commas into fake
# keywords ("major refactors" out of "Lead the design, major refactors,
# redesigns..." under a bare "RESPONSIBILITIES:" heading). Checked against
# the run of text immediately before the colon, not the whole document, so
# a real label like "HPC background:" is untouched.
_NARRATIVE_COLON_HEAD = re.compile(
    r"(?:responsibilities|role|summary|overview|about|you\s+will|you\s+are|you'll)\s*$",
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
# multi-word phrase. No trailing \b: one already sits at the end of the
# character class's own reach, and requiring a *second* word-boundary right
# after a symbol like "#" or "+" can never succeed when the very next
# character is also non-word (a comma) -- that forced "C#"/"C++" to
# backtrack down to a bare "C" instead of matching whole. Capped at
# MAX_PHRASE_WORDS, same as every other phrase heuristic here, so a real
# 4-word run like "Early Career Software Engineer" is captured (and can
# still be filtered whole, e.g. by drop_known_names) instead of fracturing
# into "Early Career Software" + a stray leftover "Engineer".
_PROPER_NOUN = re.compile(
    r"\b[A-Z][A-Za-z0-9+#]*(?:\.[A-Za-z0-9+#]+)*"
    rf"(?:[ \t]+[A-Z][A-Za-z0-9+#]*(?:\.[A-Za-z0-9+#]+)*){{0,{MAX_PHRASE_WORDS - 1}}}"
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
    # a phrase never legitimately ends on a dangling preposition
    # ("ongoing evolution of", "low-overhead solutions over") -- whatever
    # it was introducing got cut off by a list/window boundary before the
    # object arrived, so the preposition itself is never part of the term.
    while words and words[-1].lower().strip(".,") in _TRAILING_PREPOSITIONS:
        words.pop()
    return " ".join(words)


_NOISE_WORDS = _STOPWORDS | _PROCESS_NOISE | _GENERIC_MODIFIERS


def _is_plausible_keyword(phrase: str) -> bool:
    words = phrase.split()
    if not words or len(words) > MAX_PHRASE_WORDS:
        return False
    return not all(w.lower().strip(".,") in _NOISE_WORDS for w in words)


def _candidate(raw_item: str) -> str | None:
    phrase = _trim_filler(_clean_phrase(raw_item))
    return phrase if _is_plausible_keyword(phrase) else None


_MAX_LIST_ITEM_WORDS = 4

# "continuous integration for C++ codebases" -- the last item in an Oxford
# list often runs straight into the sentence's own trailing prepositional
# phrase with no comma to mark where the item actually ends. Rather than
# discarding a >4-word item outright, cut it at the last preposition that
# still leaves a short-enough prefix -- "continuous integration" is a real
# keyword, "for C++ codebases" never was part of the list.
_TRAILING_PREPOSITIONS = {
    "for", "in", "with", "on", "to", "of", "at", "by", "over", "than",
    "without", "through",
}


def _shorten_trailing_clause(phrase: str, max_words: int) -> str:
    words = phrase.split()
    if len(words) <= max_words:
        return phrase
    for i in range(min(max_words, len(words) - 1), 0, -1):
        if words[i].lower() in _TRAILING_PREPOSITIONS:
            return " ".join(words[:i])
    return phrase


_LIST_WINDOW_CHARS = 220

# A flattened page runs a section heading straight into whatever comes next
# with no punctuation at all ("...numerical simulations PREFERRED SKILLS
# AND EXPERIENCE: Expert-level...") -- a run of 2+ ALL-CAPS words is that
# transition, and is just as much a hard stop as a period, even though
# nothing but capitalization marks the seam. Single ALL-CAPS words are
# excluded (a real acronym like "C++ OR" would otherwise falsely trip this).
_HEADING_RUN = re.compile(r"[A-Z]{2,}(?:\s+[A-Z]{2,}){1,}")

# "large language models (LLMs)" -- a short acronym gloss immediately
# after the term it abbreviates is part of that same list item, not a
# separate parenthetical aside, so it must not trip the open-paren
# boundary below the way a real aside ("(favoring straightforward...)")
# should.
_INLINE_ACRONYM_GLOSS = re.compile(r"\([A-Z][A-Za-z0-9]{1,6}\)")


def _items_in_window(text: str, start: int) -> list[str]:
    window = text[start : start + _LIST_WINDOW_CHARS]
    # stop at the first sentence end, line break, semicolon, open-paren, or
    # heading-run seam -- a cue phrase immediately followed by its own
    # newline-separated bullet list (handled by _phrases_from_short_lines
    # instead), a second clause past a semicolon, a trailing parenthetical
    # aside ("...implementation (favoring straightforward...)"), or the next
    # section's own heading must not bleed into the list itself.
    boundaries = [m.start() for m in re.finditer(r"[.\n;]", window)]
    boundaries += [
        m.start()
        for m in re.finditer(r"\(", window)
        if not _INLINE_ACRONYM_GLOSS.match(window, m.start())
    ]
    boundaries += [m.start() for m in _HEADING_RUN.finditer(window)]
    boundary_pos = min(boundaries, default=None)
    has_boundary = boundary_pos is not None
    tail = window[:boundary_pos] if has_boundary else window
    items = _LIST_SPLIT.split(tail)
    if not has_boundary and items:
        # the window ended at the char cutoff, not a real sentence boundary --
        # the last split item is likely a word chopped mid-way
        # ("...one or more langu[age]s") rather than a genuine list item
        items = items[:-1]
    found = []
    for item in items:
        candidate = _candidate(item)
        if not candidate:
            continue
        # a genuine list item is short; anything longer without ever
        # hitting a comma/and/or is more likely a prose continuation
        # than a keyword ("an interest in building practical" vs "Python")
        if len(candidate.split()) > _MAX_LIST_ITEM_WORDS:
            candidate = _shorten_trailing_clause(candidate, _MAX_LIST_ITEM_WORDS)
        if len(candidate.split()) <= _MAX_LIST_ITEM_WORDS:
            found.append(candidate)
    return found


def _phrases_from_lead_in_lists(text: str) -> list[str]:
    found = []
    for match in _LIST_LEAD_IN.finditer(text):
        found.extend(_items_in_window(text, match.end()))
    for match in _GENERIC_COLON.finditer(text):
        if _NARRATIVE_COLON_HEAD.search(text[max(0, match.start() - 30) : match.start()]):
            continue
        found.extend(_items_in_window(text, match.end()))
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


# "High-performance computing (HPC) background:" -- when a posting spells
# a term out AND gives its own acronym for it, that's the posting itself
# defining a real, discrete named thing (an author doesn't bother
# acronym-defining a vague narrative phrase), so the spelled-out form is
# trusted here even where the general noise-word rules above would
# otherwise treat "computing" as too generic to keep. This is the one
# place matching.py resolves which literal form to use when a JD gives
# both -- not by preferring one shape over the other, but by requiring
# the posting's own acronym to actually match the phrase's own initials.
_ACRONYM_DEFINITION = re.compile(r"([A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,5})\s*\(([A-Z]{2,6})\)")


def _acronym_initials(words: list[str]) -> str:
    return "".join(segment[0] for word in words for segment in word.split("-") if segment).upper()


def _phrases_from_acronym_definitions(text: str) -> list[str]:
    found = []
    for match in _ACRONYM_DEFINITION.finditer(text):
        words = match.group(1).split()
        acronym = match.group(2)
        for start in range(len(words)):
            phrase_words = words[start:]
            if _acronym_initials(phrase_words) == acronym:
                found.append(" ".join(phrase_words))
                break
    return found


_PAREN_CONTENT = re.compile(r"\(([^()]{1,150})\)")
_PAREN_ASIDE_PREFIX = re.compile(
    r"^(?:e\.g\.,?|i\.e\.,?|such\s+as|including|think)\s*", re.IGNORECASE
)
_TRAILING_ETC = re.compile(r",?\s*etc\.?$", re.IGNORECASE)

# "(favoring straightforward, low-overhead solutions over complex
# abstractions or heavy STL use when they compromise speed or safety)" has
# the same comma/or shape as a real examples-list, but opens by framing a
# preference/tradeoff, not by naming things -- a real list of terms never
# opens this way.
_PAREN_NARRATIVE_PREFIX = re.compile(
    r"^(?:favoring|preferring|emphasizing|prioritizing)\b", re.IGNORECASE
)


def _phrases_from_parentheticals(text: str) -> list[str]:
    """"...or related techniques (Monte Carlo, distributed sims, etc.)" --
    a posting's own examples-in-parens are exactly the kind of concrete
    keyword a lead-in-list or generic-chain scan never reaches, since the
    outer sentence's commas belong to a different, longer list. Only
    treated as a list when it actually has comma/and/or structure --
    a bare aside like "(HPC)" or "(Starlink)" is a single term, not a list,
    and is left to the proper-noun heuristic instead."""
    found = []
    for match in _PAREN_CONTENT.finditer(text):
        inner = _TRAILING_ETC.sub("", _PAREN_ASIDE_PREFIX.sub("", match.group(1).strip())).strip()
        if not re.search(r",|\band\b|\bor\b", inner, re.IGNORECASE):
            continue
        if _PAREN_NARRATIVE_PREFIX.match(inner):
            continue
        for item in _LIST_SPLIT.split(inner):
            candidate = _candidate(item)
            if candidate and len(candidate.split()) <= _MAX_LIST_ITEM_WORDS:
                found.append(candidate)
    return found


# A hyphen or slash joining two bare words is almost always a technical
# term of art regardless of case ("real-time", "data-oriented",
# "multi-threading/concurrency", "hardware-in-the-loop") -- unlike the
# Capitalized-run heuristic above, this is the only thing in this module
# that catches lowercase compound jargon. A handful of generic hyphenated
# filler words that fit the same shape but never a "skill" are excluded
# outright rather than left for the stopword-plurality check, since a
# 2-word compound like "fast-paced" would otherwise sail through it.
_COMPOUND_CORE = re.compile(r"\b[A-Za-z]+(?:[-/][A-Za-z]+)+\b")
_COMPOUND_EXTEND_WORD = re.compile(r"^ ([A-Za-z][A-Za-z-]*)(?![A-Za-z+#])")
_COMPOUND_FILLER = {
    "fast-paced", "full-time", "part-time", "long-term", "short-term",
    "day-to-day", "up-to-date", "on-site", "off-site", "well-rounded",
    "self-motivated", "cutting-edge", "state-of-the-art", "in-house",
    "expert-level", "entry-level", "senior-level", "junior-level",
    "mid-level", "cross-functionally", "cross-functional", "problem-solving",
    "results-driven", "detail-oriented", "team-oriented", "world-class",
    "best-in-class", "high-impact", "high-value", "high-priority",
    "mission-critical", "value-added",
    # paradigm/quality adjectives with nothing after them to name (the
    # extend loop already blocks a *matching* generic noun from tacking
    # on, per _PROCESS_NOISE, but a bare occurrence with no noun at all --
    # "real-time" followed by punctuation, not a word -- needs its own
    # exclusion here since there's no second word for that check to see).
    "real-time", "high-performance", "data-oriented", "high-level",
    "low-level", "large-scale", "small-scale", "object-oriented",
    "cross-platform", "multi-platform", "performance-critical",
}
_COMPOUND_EXTEND_MAX_WORDS = 2


def _compound_phrases(text: str) -> list[str]:
    """The same compound often shows up once bare ("...high-performance
    C++...", extension blocked by the C++ that follows) and once extended
    ("high-performance simulations", "High-performance computing")
    elsewhere in the same posting -- each extended occurrence is a real,
    distinct phrase worth keeping, but a bare occurrence of a core that
    extends successfully anywhere else in the text is just the same term
    caught before its noun, so only bare occurrences get suppressed."""
    raw: list[tuple[str, str, bool]] = []
    for match in _COMPOUND_CORE.finditer(text):
        core = match.group(0)
        if core.lower() in _COMPOUND_FILLER:
            continue
        words = [core]
        pos = match.end()
        for _ in range(_COMPOUND_EXTEND_MAX_WORDS):
            extend = _COMPOUND_EXTEND_WORD.match(text[pos : pos + 30])
            if not extend or extend.group(1).lower() in _NOISE_WORDS | _TRAILING_PREPOSITIONS:
                break
            words.append(extend.group(1))
            pos += extend.end()
        candidate = _candidate(" ".join(words))
        if candidate:
            raw.append((core.lower(), candidate, len(words) > 1))
    extended_cores = {core for core, _, extended in raw if extended}
    found = []
    seen: set[str] = set()
    for core, candidate, extended in raw:
        if not extended and core in extended_cores:
            continue
        key = candidate.lower()
        if key not in seen:
            seen.add(key)
            found.append(candidate)
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


# A handful of phrases pass every structural check above (a real lead-in,
# a real comma boundary, every individual word technically not a stopword)
# and still read as narration, not a claimable skill, with no regex able
# to tell them apart from a neighboring genuine item in the same list --
# e.g. "or related techniques" sits right next to "scalable architectures"
# in an otherwise-real requirements list. Same idiom as _COMPOUND_FILLER/
# _CALENDAR_WORDS above: a small, named, hand-curated exclusion, not a
# skills dictionary -- it can only ever suppress a phrase, never grant one.
_NARRATIVE_FILLER_PHRASES = {
    "simple", "safety", "related techniques", "numerical simulations",
    "dispersion handling", "performance-oriented implementation",
    "careful performance-oriented implementation", "low-overhead solutions",
    "large-scale runs", "reliability for large-scale runs", "tooling/visualization",
    # "dynamics" alone is too vague to claim as a skill, but the same
    # posting's "(e.g., game engines, multi-body dynamics, robotics...)"
    # also yields the specific "multi-body dynamics" -- excluding the bare
    # word here (rather than after the fact) keeps _drop_redundant_superstrings
    # from doing what it normally should and preferring the shorter one,
    # which here would throw away the more specific, more useful phrase.
    "dynamics",
    # one-off compound extensions built from a company/team-specific
    # modifier ("GNC-specific", "engine-level") -- neither is a nameable
    # framework/library/language/tool, just a JD's own narrower phrasing
    # of one, and neither generalizes into a rule worth writing. Lowercase
    # to match the `phrase.lower()` key these are checked against below.
    "gnc-specific data visualization", "power/propulsion/control hardware",
    "engine-level simulation",
    # "STEM" is shaped exactly like a real acronym (short, all-caps) and
    # passes _looks_like_acronym on that basis alone, but it names a
    # degree field ("Bachelor's in a STEM discipline"), not a technology.
    "stem",
    # domain-specific team/discipline acronyms too narrow to generalize as
    # a resume-worthy skill outside this one posting's own org chart
    "gnc", "stl",
    # short, acronym-shaped, and structurally indistinguishable from a
    # real tech acronym, but a degree ("BS/MS/PhD in Computer Science") or
    # a bare, too-generic-to-name-alone abbreviation, not a technology
    "phd", "ms", "bs", "ba", "mba", "ui", "ip",
}

# Almost every US job posting ends with the same non-technical tail:
# compensation/benefits, then legal/export-control/EEO boilerplate. None of
# it is ever a real requirement -- it's where things like "Pay Range",
# "Employee Stock Purchase Plan", "Seattle", "Refugee", "U.S.C", "Asylee"
# come from, all four heuristics above being equally happy to extract a
# Capitalized run, a colon-list item, or a short line from a legal
# paragraph as from a real qualifications section. Cutting the text off at
# the first sign of this tail -- rather than trying to word-list every
# possible benefit/legal term one at a time -- fixes every heuristic at
# once, the same way _strip_chrome_sections in core/jd_text.py removes a
# "Related Jobs" carousel structurally instead of denylisting its content.
# Anchored to distinctive multi-word legal/HR phrasing, not solo words like
# "benefits" or "requirements" that also appear naturally in real
# technical prose ("the benefits of a data-oriented design...").
_BOILERPLATE_SECTION_START = re.compile(
    r"\b(?:"
    r"compensation\s+and\s+benefits|compensation\s*&\s*benefits|"
    r"pay\s+range|salary\s+range|total\s+rewards\s+package|"
    r"itar\s+requirements|export\s+control|"
    r"u\.?s\.?\s+government\s+export\s+regulations|"
    r"equal\s+opportunity\s+employer|equal\s+employment\s+opportunity|"
    r"affirmative\s+action|reasonable\s+accommodation|"
    r"additional\s+requirements"
    r")\b",
    re.IGNORECASE,
)


def _strip_boilerplate_tail(text: str) -> str:
    match = _BOILERPLATE_SECTION_START.search(text)
    return text[: match.start()] if match else text


# No structural rule can tell "Docker" (a tool) from "Monte Carlo" (a
# named mathematical technique) apart -- both are a plain capitalized
# proper noun, or "multi-body dynamics" (a physics concept) from a real
# multi-word tool name -- both are an ordinary lowercase phrase. A real
# acronym is the one shape that's a reliable enough signal on its own
# (GNC, HITL, STL, HPC, STEM, C++, C#): mostly-uppercase letters, or a
# language-symbol suffix, and short -- a full ALL-CAPS section heading
# ("REQUIREMENTS") is long enough to fail the length check on its own.
_ACRONYM_MAX_LETTERS = 8


def _looks_like_acronym(phrase: str) -> bool:
    letters = [c for c in phrase if c.isalpha()]
    if not letters or len(letters) > _ACRONYM_MAX_LETTERS:
        return False
    if any(c in "+#" for c in phrase):
        return True
    return sum(c.isupper() for c in letters) / len(letters) >= 0.6


def _known_technical_span(phrase: str) -> str | None:
    """None if nothing in `phrase` is a known technology; otherwise the
    longest recognized contiguous span, in the phrase's own original
    casing -- trimmed, not just approved whole.

    "Machine Learning Engineer" (a proper-noun run swallowing a title
    word) becomes "Machine Learning"; "Firebase Crashlytics" (a known
    single word plus an uncurated one) becomes "Firebase"; "agile
    development methodologies" becomes "Agile", not the whole noisy
    phrase -- a bare common word rescuing a longer phrase wholesale would
    defeat the entire point of gating on this list, but trimming down to
    just the part that's actually recognized has no such downside."""
    if phrase.lower() in ALL_TECH_NAMES or _looks_like_acronym(phrase):
        return phrase
    words = phrase.split()
    lower_words = [w.lower() for w in words]
    best: str | None = None
    for name in ALL_TECH_NAMES:
        name_words = name.split()
        n = len(name_words)
        if n > len(lower_words):
            continue
        for i in range(len(lower_words) - n + 1):
            if lower_words[i : i + n] == name_words:
                span = " ".join(words[i : i + n])
                if best is None or len(span) > len(best):
                    best = span
                break
    return best


def extract_keywords(text: str) -> list[str]:
    """Candidate keyword phrases straight out of the posting's own text.
    Deterministic (the same text always yields the same list) and literal
    (every result is a real substring of `text`, first-seen order, capped
    at MAX_KEYWORDS so a long posting doesn't flood the score card)."""
    text = _strip_boilerplate_tail(text)
    # A phrase the posting itself acronym-defines is trusted outright,
    # bypassing the tech-names gate below -- see _phrases_from_acronym_
    # definitions for why that structural signal is reliable on its own.
    acronym_defined = _phrases_from_acronym_definitions(text)
    acronym_defined_keys = {p.lower() for p in acronym_defined}
    # Named technologies/acronyms are rarely wrong and there are usually
    # few of them, so they all make the cut first. Everything else is
    # round-robined one-per-heuristic instead of concatenated -- a strict
    # cap on a concatenated list means whichever heuristic happens to run
    # last (here, short lines) never contributes at all, even though its
    # own items are just as real as the first heuristic's 30th item.
    other_buckets = [
        _compound_phrases(text),
        _phrases_from_lead_in_lists(text),
        _phrases_from_parentheticals(text),
        _phrases_from_short_lines(text),
    ]
    candidates = [
        *_proper_noun_phrases(text),
        *acronym_defined,
        *(
            phrase
            for round_ in zip_longest(*other_buckets)
            for phrase in round_
            if phrase is not None
        ),
    ]
    seen: set[str] = set()
    deduped: list[str] = []
    for phrase in candidates:
        key = phrase.lower()
        if key in acronym_defined_keys:
            kept = phrase if key not in _NARRATIVE_FILLER_PHRASES else None
        else:
            span = _known_technical_span(phrase)
            kept = span if span and span.lower() not in _NARRATIVE_FILLER_PHRASES else None
        if kept is None:
            continue
        kept_key = kept.lower()
        if kept_key not in seen:
            seen.add(kept_key)
            deduped.append(kept)
    return _drop_redundant_superstrings(deduped)[:MAX_KEYWORDS]


_NAME_SEGMENT_SPLIT = re.compile(r",|\s[-|]\s|[()]")


def drop_known_names(keywords: list[str], *names: str) -> list[str]:
    """Neither the posting's own employer name nor its own job title is a
    skill a candidate could ever claim -- filtered out wherever a keyword
    IS the posting's own employer name or job title, or one of its natural
    comma/dash/parenthetical-separated segments, verbatim.

    "Software Engineer, User Frameworks" splits into "Software Engineer"
    and "User Frameworks" -- both are still just the title, not a claim.
    "Software Engineer, C++ Simulations (Starlink)" also splits out
    "Starlink" on its own -- a team/product name parenthesized onto a
    title names the team, not a skill, same as the title's other segments.
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
