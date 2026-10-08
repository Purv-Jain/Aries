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

__all__ = ["split_sentences", "chunk_page", "chunk_pages"]

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
            previous_start, previous_end = spans[-1]
            spans[-1] = (previous_start, total)
            break

        spans.append((start, end))
        if end >= total:
            break
        start = end - config.overlap_words
        if start <= spans[-1][0]:  # pragma: no cover - guarded by ChunkConfig validation
            start = spans[-1][0] + 1

    chunks: list[EvidenceChunk] = []
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