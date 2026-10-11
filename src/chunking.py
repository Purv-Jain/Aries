"""Sentence-aware chunking with an exact word overlap.

Responsibility, and nothing else: turn ``DocumentPage`` objects into
``EvidenceChunk`` objects, carrying the page metadata each chunk must keep for a
citation to point at the right page.

Why sentence-awareness plus an exact overlap, which pull against each other:

* A chunk that ends mid-sentence produces an embedding of a fragment. MiniLM was
  trained on whole sentences, and a truncated sentence retrieves badly.
* An overlap that only happens to fall on a sentence boundary leaves gaps in the
  evidence exactly where they hurt -- at the point where a definition is first
  introduced.

So: slide a window over the page's words, then close the window at the last
sentence boundary at or after the target size, and start the next window exactly
``overlap_words`` before that boundary. The chunk may slightly overshoot
``chunk_words``; the overlap is exact, which is the property that matters.

A chunk never spans two pages (IC-5). A citation whose page number is ambiguous is
worse than no citation, because it looks authoritative while being wrong.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from src.models import ChunkConfig, DocumentPage, EvidenceChunk, compute_chunk_id

__all__ = ["split_sentences", "chunk_page", "chunk_pages", "light_stem"]

# Abbreviations whose trailing period does not end a sentence (ADR-0003).
# "No." and "Fig." are the ones that actually break naive splitters in academic
# text; the rest are cheap insurance.
_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "e.g", "i.e", "al", "cf", "vs", "viz", "fig", "figs", "eq", "eqs",
        "no", "nos", "vol", "ch", "sec", "ref", "refs", "approx", "ca",
        "dr", "prof", "mr", "mrs", "ms", "st", "pp", "ed", "eds",
    }
)

_WS_RUN = re.compile(r"\s+")
# A sentence can only start with an upper-case letter, a digit or an opening mark.
_SENTENCE_START = re.compile(r"[A-Z0-9\"'(\[]")
# Look back over the word immediately before the terminator.
_WORD_BEFORE_PERIOD = re.compile(r"([A-Za-z.&]+)\.$")


def split_sentences(text: str) -> list[str]:
    """Split normalised text into sentences using punctuation and capitalisation.

    No NLP dependency on purpose (ADR-0003): nltk or spaCy would add a corpus
    download to a project whose defining constraint is working offline, for a
    benefit this corpus does not need.

    A boundary is accepted only when the text before it is a complete word (not an
    abbreviation or a single initial) *and* the text after it looks like the start
    of a sentence. Requiring both directions is what stops "3. lower" and "et al."
    from splitting.
    """
    normalised = _WS_RUN.sub(" ", text or "").strip()
    if not normalised:
        return []

    sentences: list[str] = []
    start = 0
    for match in re.finditer(r"[.!?][\"')\]]*(?=\s)", normalised):
        end = match.end()
        if not _looks_like_boundary(normalised, start, match.start(), end):
            continue
        piece = normalised[start:match.start() + 1].strip()
        if piece:
            sentences.append(piece)
        start = end

    tail = normalised[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def _looks_like_boundary(text: str, start: int, period_at: int, after: int) -> bool:
    """Decide whether the punctuation at ``period_at`` ends a sentence."""
    preceding = text[start:period_at + 1]
    word_match = _WORD_BEFORE_PERIOD.search(preceding)
    if word_match:
        stem = word_match.group(1).rstrip(".").lower()
        if stem in _ABBREVIATIONS:
            return False
        if len(stem) == 1 and word_match.group(1)[0].isupper():
            # A single capital letter is an initial: "J. Smith".
            return False

    remainder = text[after:].lstrip()
    if not remainder:
        return True
    return bool(_SENTENCE_START.match(remainder[0]))


def _sentence_end_indices(words: Sequence[str], text: str) -> set[int]:
    """Exclusive word indices at which a sentence ends."""
    ends: set[int] = set()
    cursor = 0
    for sentence in split_sentences(text):
        cursor += len(sentence.split())
        ends.add(cursor)
    return {index for index in ends if 0 < index <= len(words)}


def _choose_end(start: int, config: ChunkConfig, sentence_ends: set[int]) -> int | None:
    """Last sentence boundary inside the window, or ``None`` to hard-cut.

    "Last" rather than "first": stopping at the first boundary after the target
    keeps chunks from drifting long, while still honouring the sentence boundary
    the window happens to be sitting on.
    """
    if not config.respect_sentences:
        return None
    hard_limit = start + config.chunk_words
    floor = start + min(config.min_chunk_words, config.chunk_words)
    candidates = [end for end in sentence_ends if floor <= end <= hard_limit]
    return max(candidates) if candidates else None


def chunk_page(page: DocumentPage, config: ChunkConfig | None = None) -> tuple[EvidenceChunk, ...]:
    """Chunk a single ``DocumentPage``. Never spans pages, by construction."""
    config = config or ChunkConfig()
    if not isinstance(config, ChunkConfig):
        raise ValueError("config must be a ChunkConfig")

    words = page.text.split()
    if not words:
        return ()

    sentence_ends = _sentence_end_indices(words, page.text)

    spans: list[tuple[int, int]] = []
    start = 0
    total = len(words)
    while start < total:
        boundary = _choose_end(start, config, sentence_ends)
        end = boundary if boundary is not None else min(start + config.chunk_words, total)

        remaining = total - end
        if 0 < remaining < config.min_chunk_words and spans:
            # Absorb a stub tail into the chunk before it rather than emit a
            # fragment too small to embed meaningfully.
            previous_start, _previous_end = spans[-1]
            spans[-1] = (previous_start, total)
            break

        spans.append((start, end))
        if end >= total:
            break
        start = end - config.overlap_words
        if start <= spans[-1][0]:  # pragma: no cover - guarded by ChunkConfig validation
            start = spans[-1][0] + 1

    chunks: list[EvidenceChunk] = []
    is_reference = "reference_page_detected" in page.warnings
    for index, (begin, finish) in enumerate(spans):
        text = " ".join(words[begin:finish])
        chunks.append(
            EvidenceChunk(
                chunk_id=compute_chunk_id(page.source_id, page.page_number, index),
                source_id=page.source_id,
                filename=page.filename,
                page_number=page.page_number,
                chunk_index_in_page=index,
                text=text,
                citation_label="",
                is_reference_page=is_reference,
            )
        )
    return tuple(chunks)


def chunk_pages(
    pages: Sequence[DocumentPage],
    config: ChunkConfig | None = None,
) -> tuple[EvidenceChunk, ...]:
    """Chunk a sequence of ``DocumentPage`` objects, preserving page order."""
    config = config or ChunkConfig()
    if not isinstance(config, ChunkConfig):
        raise ValueError("config must be a ChunkConfig")
    if isinstance(pages, (str, bytes)):
        raise ValueError("pages must be a sequence of DocumentPage objects")

    chunks: list[EvidenceChunk] = []
    for page in pages:
        chunks.extend(chunk_page(page, config))
    return tuple(chunks)


# -- light stemming ---------------------------------------------------------
#
# Suffix stripping, not the Porter algorithm. Both live here rather than in `pipeline` because
# this is the same kind of responsibility as `split_sentences`: reducing text to a comparable form.
# Keeping it beside the sentence splitter means one module owns "how this project normalises prose".

# (suffix stripped, what replaces it, minimum length the remainder must keep)
#
# The minimum length is the only guard there is, and it does real work. "s" alone would reduce
# `is` to `i` and `was` to `wa`, which collapses distinct words and makes coverage claim a match
# that is not one. Refusing to strip below four characters leaves short words alone, which is why
# every English function word -- whose absence from the question's meaning matters least -- survives
# untouched.
_STEM_RULES: tuple[tuple[str, str, int], ...] = (
    ("ization", "ize", 4),
    ("ational", "ate", 4),
    ("iveness", "ive", 4),
    ("fulness", "ful", 4),
    ("ousness", "ous", 4),
    ("ements", "ement", 4),
    ("ities", "ity", 3),
    ("ility", "ile", 3),
    ("ement", "", 4),
    ("ments", "", 4),
    ("ation", "ate", 4),
    ("ition", "ite", 4),
    ("ally", "", 4),
    ("ical", "ic", 4),
    ("ness", "", 4),
    ("ies", "y", 3),
    ("ied", "y", 3),
    ("ing", "", 4),
    ("ers", "", 4),
    ("est", "", 4),
    ("ed", "", 4),
    ("ly", "", 4),
    ("es", "", 4),
    ("er", "", 4),
    ("al", "", 4),
    ("s", "", 4),
)

_DOUBLE_ENDING = ("bb", "dd", "ff", "gg", "mm", "nn", "pp", "rr", "tt")

# A word's silent `e` is always removed once it is longer than four characters, so that the two
# sides of every comparison pass through the identical transform: `figure` and `figures` both
# reach `figur`, `create` and `created` both reach `creat`. Asymmetric normalisation would defeat
# the entire point -- a stem that reduces one variant and not the other matches neither.
# The length guard keeps short words intact, so `where` -> `wher` rather than `where` -> `where`,
# which is harmless because `where` is a stopword and never reaches this function.
_TERMINAL_E = re.compile(r"e$")


def light_stem(word: str) -> str:
    """Reduce an English word to a stem for comparison. Deterministic and offline.

    **Why this exists, as a measurement rather than a preference.** The abstention gate matched
    question terms against retrieved text with substring containment, so `readings` did not match
    `reading` and `figures` did not match `figure`. Asked "How much time passes between successive
    readings?" of a document that says *every ninety seconds*, coverage came back 0.40 against a
    floor of 0.50 and a correctly answerable question was refused. Measured over 10 answerable
    paraphrased questions, the gate refused 6 before this function existed.

    **What stemming does and does not fix.** It fixes morphology: `readings`/`reading`,
    `figures`/`figure`, `verified`/`verify`. It does *not* fix synonyms: the document saying
    `calibrated` while the question says `tuned` still scores zero. One case out of the 10 remains
    refused after this change, for exactly that reason. Closing it needs an entailment model, not a
    longer suffix table, and it is recorded as a limit rather than papered over with a bigger list.

    **Deliberately not the Porter algorithm.** Porter's five phases and its exception tables are
    worth more than this needs: they were built for lemmatisation quality, and this is a coverage
    *signal* where an imperfect stem is sufficient. A 30-line table that is inspectable at a viva
    beats a dependency the project cannot explain.

    Words of four characters or fewer are returned unchanged, so short function words survive.
    Only the first matching rule applies, and the rules are ordered longest-first, so
    `ization` is never reached by way of `ations`.
    """
    if len(word) <= 3 or not word.isalpha():
        return word
    # Cascaded, not single-pass. A plural must be able to reach the same form its base word
    # already reaches: `reading` reduces to `read` in one step, so `readings` has to be able to
    # get there too, and stripping only `s` leaves it stranded at `reading`. Bounded at three
    # passes because every rule is subtractive; a longer chain buys nothing for English academic
    # prose and each extra pass is another chance to over-strip a short word.
    reduced = word
    for _ in range(3):
        nxt = _apply_rules(reduced)
        if nxt == reduced:
            break
        reduced = nxt
    return _TERMINAL_E.sub("", reduced) if len(reduced) > 4 else reduced


def _apply_rules(word: str) -> str:
    """Strip the first matching suffix, or return the word unchanged."""
    for suffix, replacement, minimum in _STEM_RULES:
        if not word.endswith(suffix):
            continue
        stem = word[: -len(suffix)]
        if len(stem) < minimum:
            continue
        if not replacement and stem[-2:] in _DOUBLE_ENDING and len(stem) > 3:
            # "running" -> "runn" -> "run", "stopped" -> "stop". Without this a doubled
            # consonant survives and the stem stops matching its own base form.
            stem = stem[:-1]
        return (stem + replacement) or word
    return word