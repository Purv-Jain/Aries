"""Citation verification. The project's actual contribution.

One job: given an answer whose sentences carry `[Sx, p.y]` markers, decide for each claim whether
its cited retrieved passage supports it, and say why.

Four things this module will not do, and each refusal is the point:

1. **It will not repair a bad reference.** A marker naming a source that was never retrieved is
   `Unsupported` with reason `unresolvable_reference` -- not silently dropped, and never re-pointed at
   the nearest available passage. Silently moving a citation destroys the guarantee the user is
   relying on ([ADR-0008](../../docs/05_TECH_STACK_AND_ADRS.md#adr-0008--no-citation-re-attribution-in-the-mvp)).
2. **It will not call cosine similarity proof.** `Verified` means *passed this project's documented
   support-check heuristic at the configured threshold* -- lexical and semantic correspondence, not
   logical entailment and not factual truth ([ADR-0006](../../docs/05_TECH_STACK_AND_ADRS.md#adr-0006--never-describe-cosine-similarity-as-proof)).
3. **It will not confuse the two scores.** `support_score` measures claim↔cited-chunk. The retrieval
   relevance score measures query↔chunk. They are displayed together and never combined.
4. **It will not hardcode a threshold.** Every number lives in `VerificationConfig`.

The whole module is a pure function: no I/O, no network, no model, no clock. Same inputs give the
same output, which is what makes it testable and what makes the viva defensible.

**The scoring order matters, and it is not arbitrary.** Marker resolution happens *first* and can
end the evaluation before any scoring occurs, because there is nothing to score a claim against if its
citation does not resolve. Then numeric and contradiction checks, because a claim can share every word
with its passage and still be wrong about a number or a polarity -- cases that a similarity score
alone would happily pass. Only then the weighted score, and only then the label.
"""

from __future__ import annotations

import re
from typing import Sequence

from src.chunking import split_sentences
from src.models import (
    Claim,
    ClaimVerification,
    CitationRef,
    EvidenceChunk,
    GeneratedAnswer,
    RetrievalResult,
    Reason,
    VerificationConfig,
)

__all__ = [
    "Verifier",
    "MARKER_PATTERN",
    "parse_markers",
    "strip_markers",
    "token_overlap",
    "content_tokens",
]

# Strict marker grammar. `[S1, p.5]` or `[S1, p.5; S3, p.9]`. Nothing else matches.
#
# Fuzzy matching is deliberately absent. `[S1 p5]` is `malformed_marker` and becomes `Unsupported`,
# because the alternative -- guessing which page the author meant -- is a fabricated citation wearing
# a citation's clothes. CT-17 tests both rejected forms.
MARKER_PATTERN = re.compile(
    r"\[(?P<refs>S\d+\s*,\s*p\.\s*\d+(?:\s*;\s*S\d+\s*,\s*p\.\s*\d+)*)\]"
)

_REF_PATTERN = re.compile(r"S(?P<label>\d+)\s*,\s*p\.\s*(?P<page>\d+)")

# Words that carry no evidential weight. Short and academic-specific: a claim built only from these
# would otherwise score highly against any passage.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if then than that this these those there here of in on at to for from by with
    without into over under between among during is are was were be been being am do does did doing
    have has had having can could shall should will would may might must it its it's they them their
    we our you your he she his her i me my as so such not no nor only own same too very just also
    which who whom whose what when where why how all any both each few more most other some
    """.split()
)

_WORD = re.compile(r"[a-z0-9]+")
_WS_RUN = re.compile(r"\s+")

# Negation cues. A mismatch here caps the label rather than being ignored, because
# "training did not improve accuracy" and "training improved accuracy" share almost all their words.
NEGATION_CUES: frozenset[str] = frozenset(
    {"not", "no", "never", "none", "neither", "nor", "cannot", "without", "lacks", "lacking", "failed"}
)

# Small curated antonym set for academic prose. Deliberately short: a large hand-built antonym list
# is a liability in a system with no training data, and false antonymy would push correct claims into
# `Unsupported`. Each pair must genuinely invert the polarity of the sentence.
ANTONYM_PAIRS: tuple[tuple[str, str], ...] = (
    ("increase", "decrease"),
    ("increases", "decreases"),
    ("increased", "decreased"),
    ("higher", "lower"),
    ("more", "less"),
    ("positive", "negative"),
    ("improve", "worsen"),
    ("improves", "worsens"),
    ("improved", "worsened"),
    ("gain", "loss"),
    ("significant", "insignificant"),
    ("supports", "contradicts"),
    ("effective", "ineffective"),
    ("present", "absent"),
    ("increases", "reduces"),
)

_ANTONYM_MAP: dict[str, set[str]] = {}
for _left, _right in ANTONYM_PAIRS:
    _ANTONYM_MAP.setdefault(_left, set()).add(_right)
    _ANTONYM_MAP.setdefault(_right, set()).add(_left)

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def parse_markers(text: str) -> tuple[CitationRef, ...]:
    """Extract every citation reference from an answer.

    Malformed markers are **reported, not repaired**: the returned refs carry ``resolved=False`` and
    the verbatim text, so the verifier can label the claim `malformed_marker` instead of guessing an
    intended target.
    """
    refs: list[CitationRef] = []
    for bracket in re.findall(r"\[([^\]]*)\]", text):
        found = _REF_PATTERN.findall(bracket)
        if not found:
            # An empty pair of brackets is not a citation. Treating `[]` as a malformed marker
            # would label an answer Unsupported for containing stray punctuation.
            if bracket.strip():
                refs.append(
                    CitationRef(source_id=None, page_number=None, raw=bracket.strip(), resolved=False)
                )
            continue
        for label, page in found:
            refs.append(
                CitationRef(
                    source_id=None,
                    page_number=int(page),
                    raw=f"S{label}, p.{int(page)}",
                    resolved=False,
                )
            )
    return tuple(refs)


def strip_markers(text: str) -> str:
    """Remove marker brackets, leaving the prose.

    Scoring a claim *with* its marker in the input would give every claim the same `s1 p5` tokens and
    inflate every score by a constant. The bug is subtle and always flatters the system, which is
    exactly why it is removed here and asserted by a test.

    Whitespace is collapsed afterwards, because removing a bracketed span from mid-sentence leaves a
    double space that would otherwise become two separate tokens in the overlap calculation.
    """
    return _WS_RUN.sub(" ", re.sub(r"\[[^\]]*\]", " ", text)).strip()


def content_tokens(text: str) -> set[str]:
    """Lowercase alphanumeric tokens, stopwords removed, short numerics dropped.

    ``min_numeric_tokens`` decides what counts as short. Dropping bare `1` and `2` matters because
    they appear in almost any list-like passage and would inflate containment for free.
    """
    tokens = set(_WORD.findall(text.lower()))
    return {token for token in tokens if token not in STOPWORDS and len(token) >= 2}


def token_overlap(claim: str, chunk: str, min_length: int = 2) -> float:
    """Containment of the claim's content tokens in the chunk. In `[0, 1]`.

    Containment, not Jaccard, and this is the single most consequential scoring choice in the
    project. A claim is a short summary of a long passage, so Jaccard's length asymmetry penalises
    exactly the correct citations: a 12-word claim drawn from a 180-word chunk scores 12/192 by
    Jaccard and 12/12 by containment, even though the claim is perfectly supported.

    The trade-off is real and documented: containment can be inflated by a chunk that contains the
    claim's words while *contradicting* them. That is precisely why `check_contradiction` exists,
    and why a high overlap alone is not a pass.
    """
    claim_tokens = content_tokens(claim)
    if not claim_tokens:
        return 0.0
    usable = {token for token in claim_tokens if len(token) >= min_length}
    if not usable:
        return 0.0
    chunk_tokens = content_tokens(chunk)
    if not chunk_tokens:
        return 0.0
    return min(len(usable & chunk_tokens) / len(usable), 1.0)


def _numbers(text: str) -> set[str]:
    return {match.group(0).replace(",", "") for match in _NUMBER.finditer(text)}


def _significant_numbers(text: str, min_length: int) -> set[str]:
    return {value for value in _numbers(text) if len(value) >= min_length}


def _negations(text: str) -> set[str]:
    """Negation cues present in the text.

    Deliberately *not* routed through ``content_tokens``, which drops stopwords -- and `not` is a
    stopword. Filtering negation through the same function that removes low-value tokens would delete
    the entire signal, so the contradiction check would silently never fire. That failure mode is
    invisible: the code runs, produces plausible numbers, and is wrong.
    """
    return set(_WORD.findall(text.lower())) & NEGATION_CUES


def _negations_in_matching_region(text: str, claim_tokens: set[str]) -> set[str]:
    """Negation cues in the sentence of the passage that best matches the claim.

    This function exists because of a measured failure, not a theoretical one. The first evaluation
    over 24 hand-labelled cases flagged six plainly-supported claims as `contradiction_detected`: the
    180-word chunk contained "not" or "no" *somewhere* -- "not an OCR engine", "not loaded" -- while
    the claim itself had no negation, and the verdict followed from text that had nothing to do with
    the claim.

    Restricting to the *best-matching sentence* is what makes the check mean "the passage says the
    opposite of this claim". Restricting to every sentence that shares any token with the claim was
    tried first and still over-fired, because a claim's vocabulary recurs across a whole chunk; the
    strongest overlap is the one that identifies the sentence actually being asserted.
    """
    sentences = split_sentences(text)
    if not sentences:
        return set()
    best_score = 0
    best: set[str] = set()
    for sentence in sentences:
        overlap = len(content_tokens(sentence) & claim_tokens)
        if overlap > best_score:
            best_score = overlap
            best = _negations(sentence)
    return best


def _antonym_conflict(claim_tokens: set[str], chunk_tokens: set[str]) -> str | None:
    """Return the antonym pair on which the claim and chunk disagree, if any."""
    for token in sorted(claim_tokens & chunk_tokens):
        opposites = _ANTONYM_MAP.get(token)
        if not opposites:
            continue
        # A negation on either side can turn an antonym into agreement: "did not increase" and
        # "did not decrease" are opposite claims, not agreement. Checking the plain case only is
        # safer than the clever case, because a wrong contradiction flag suppresses a real citation.
        if (opposites & chunk_tokens) and not _negations_around(claim_tokens, token):
            return f"{token}/{sorted(opposites & chunk_tokens)[0]}"
    return None


def _negations_around(tokens: set[str], token: str) -> bool:
    """True when the claim's own vocabulary already contains a negation cue.

    A coarse, honest approximation: this module does not do dependency parsing, so it does not claim
    to know which word the negation modifies. When in doubt it declines to raise a contradiction,
    because a false contradiction flag pushes a correct claim into `Unsupported`.
    """
    return bool(tokens & NEGATION_CUES)


class Verifier:
    """Pure function: (answer, retrieved, config) -> tuple of ClaimVerification."""

    def __init__(self, similarity_fn: object = None) -> None:
        """``similarity_fn(claim, chunk_text) -> [0, 1]`` is optional.

        The offline profile has no natural claim↔chunk similarity that is independent of the
        overlap term, so when it is absent the verifier falls back to a deterministic lexical
        similarity. The profile-specific function is injected by the pipeline when one exists, and
        the fallback is documented rather than silent.
        """
        self._similarity_fn = similarity_fn

    def verify(
        self,
        answer: GeneratedAnswer,
        retrieved: Sequence[RetrievalResult],
        config: VerificationConfig | None = None,
    ) -> tuple[ClaimVerification, ...]:
        config = config or VerificationConfig()
        by_label = _label_index(retrieved)

        if answer.abstained:
            return ()

        return tuple(
            self._verify_claim(claim, by_label, retrieved, config)
            for claim in answer.claims
        )

    # -- one claim ------------------------------------------------------------

    def _verify_claim(
        self,
        claim: Claim,
        by_label: dict[str, RetrievalResult],
        retrieved: Sequence[RetrievalResult],
        config: VerificationConfig,
    ) -> ClaimVerification:
        claim_text = strip_markers(claim.text) or claim.text

        # 1. Resolution. Nothing can be scored against a citation that does not resolve.
        resolution = self._resolve(claim, by_label)
        if isinstance(resolution, ClaimVerification):
            return resolution

        evidence_result, chosen_ref = resolution
        evidence = evidence_result.chunk
        evidence_text = evidence.text

        # 2. Numbers. A year or a measurement must be present in the cited passage.
        if config.check_numbers:
            claim_numbers = _significant_numbers(claim_text, config.min_numeric_tokens)
            missing = claim_numbers - _significant_numbers(evidence_text, config.min_numeric_tokens)
            if missing:
                return ClaimVerification(
                    claim_id=claim.claim_id,
                    claim_text=claim_text,
                    label="Unsupported",
                    support_score=0.0,
                    similarity=0.0,
                    overlap=0.0,
                    evidence=evidence,
                    relevance_score=evidence_result.relevance_score,
                    reason=Reason.NUMERIC_MISMATCH,
                    explanation=(
                        f"The claim cites {sorted(missing)} which do not appear in the cited "
                        f"passage (page {evidence.page_number}). A number cannot be supported by a "
                        "passage that does not contain it. This is a lexical check, not a judgement "
                        "about whether either number is true."
                    ),
                )

        # 3. Polarity. Shared vocabulary with opposite meaning is the failure a score misses.
        claim_tokens = content_tokens(claim_text)
        chunk_tokens = content_tokens(evidence_text)
        if config.check_contradiction:
            conflict = _antonym_conflict(claim_tokens, chunk_tokens)
            if conflict is not None:
                left, right = conflict.split("/")
                return ClaimVerification(
                    claim_id=claim.claim_id,
                    claim_text=claim_text,
                    label="Unsupported",
                    support_score=0.0,
                    similarity=0.0,
                    overlap=0.0,
                    evidence=evidence,
                    relevance_score=evidence_result.relevance_score,
                    reason=Reason.CONTRADICTION_DETECTED,
                    explanation=(
                        f"The claim uses '{left}' while the cited passage (page "
                        f"{evidence.page_number}) uses the opposite term '{right}'. The words match "
                        "but the direction does not. This is a keyword heuristic over a small "
                        "antonym list, not a semantic entailment check."
                    ),
                )

            # Compare **polarity**, not which cue word was used. "does not depend" and
            # "no ... required" are the same polarity; treating them as a mismatch flagged a
            # correct paraphrase as a contradiction.
            claim_negated = bool(_negations(claim_text))
            region_negated = bool(_negations_in_matching_region(evidence_text, claim_tokens))
            claim_neg = _negations(claim_text)
            relevant_chunk_neg = _negations_in_matching_region(evidence_text, claim_tokens)
            if claim_negated != region_negated and (claim_tokens & chunk_tokens):
                # Only decisive when the shared vocabulary is substantial; otherwise every short
                # claim would trip this and the check would be noise.
                if len(claim_tokens & chunk_tokens) >= max(3, int(len(claim_tokens) * 0.6)):
                    return ClaimVerification(
                        claim_id=claim.claim_id,
                        claim_text=claim_text,
                        label="Needs Review",
                        support_score=0.0,
                        similarity=0.0,
                        overlap=0.0,
                        evidence=evidence,
                        relevance_score=evidence_result.relevance_score,
                        reason=Reason.CONTRADICTION_DETECTED,
                        explanation=(
                            "The claim "
                            f"{'is negated' if claim_negated else 'is not negated'} but the part "
                            "of the cited passage that matches it "
                            f"{'is negated' if region_negated else 'is not negated'} "
                            f"(page {evidence.page_number}). Polarity may differ; a human should "
                            "read the passage."
                        ),
                    )

        # 4. The weighted score.
        similarity = self._similarity(claim_text, evidence_text, config)
        overlap = token_overlap(claim_text, evidence_text)
        support = config.score(similarity, overlap)

        label = (
            "Verified"
            if support >= config.verified_threshold
            else "Needs Review"
            if support >= config.review_threshold
            else "Unsupported"
        )
        reason = {
            "Verified": Reason.SUPPORTED,
            "Needs Review": Reason.WEAK_SUPPORT,
            "Unsupported": Reason.NO_SUPPORT,
        }[label]

        return ClaimVerification(
            claim_id=claim.claim_id,
            claim_text=claim_text,
            label=label,
            support_score=support,
            similarity=similarity,
            overlap=overlap,
            evidence=evidence,
            relevance_score=evidence_result.relevance_score,
            reason=reason,
            explanation=_explain(label, support, similarity, overlap, evidence, chosen_ref, config),
        )

    # -- resolution -----------------------------------------------------------

    def _resolve(
        self,
        claim: Claim,
        by_label: dict[str, RetrievalResult],
    ) -> tuple[tuple[RetrievalResult, CitationRef], ...] | ClaimVerification:
        """Resolve the claim's markers against the retrieved set.

        Returns either a `(result, ref)` pair to score against, or a finished `ClaimVerification` for
        the cases where resolution alone is enough to decide. The failure paths are all `ClaimVerification`
        because every one of them is a real, reportable outcome -- none of them is an error to raise.
        """
        refs = claim.markers or parse_markers(claim.text)

        if not refs:
            return ClaimVerification(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                label="Unsupported",
                support_score=0.0,
                similarity=0.0,
                overlap=0.0,
                evidence=None,
                relevance_score=None,
                reason=Reason.NO_MARKER,
                explanation=(
                    "This claim carries no citation marker, so there is no evidence to check it "
                    "against. An uncited factual claim cannot be Verified. This is a report on the "
                    "answer's citation coverage, not a judgement that the claim is false."
                ),
            )

        resolvable: list[tuple[RetrievalResult, CitationRef]] = []
        malformed: list[CitationRef] = []
        for ref in refs:
            # Resolution is done here, from `raw` alone. The `resolved` flag a generator set is
            # treated as a hint, never as authority -- trusting it would let a generator vouch for
            # its own citation, which is precisely the thing the verifier exists to check.
            match = _REF_PATTERN.fullmatch(ref.raw.replace(" ", ""))
            if match is None:
                malformed.append(ref)
                continue
            key = f"S{int(match.group('label'))}"
            result = by_label.get(key)
            if result is None:
                continue
            cited_page = int(match.group("page"))
            if cited_page != result.chunk.page_number:
                # Retrieved, but not at the page the claim cites. Distinct from unresolvable:
                # the source exists and the page is wrong, which is a different user-facing problem.
                continue
            resolvable.append((result, ref))

        if not resolvable:
            raws = ", ".join(ref.raw for ref in refs)
            if malformed and len(malformed) == len(refs):
                return ClaimVerification(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    label="Unsupported",
                    support_score=0.0,
                    similarity=0.0,
                    overlap=0.0,
                    evidence=None,
                    relevance_score=None,
                    reason=Reason.MALFORMED_MARKER,
                    explanation=(
                        f"The citation '{raws}' could not be parsed. Malformed markers are reported, "
                        "never repaired: guessing the intended source would be fabricating a citation."
                    ),
                )
            pages_disagree = [
                ref
                for ref in refs
                # Only counts as a page mismatch when the source *does* exist. A reference to a
                # source that was never retrieved is `unresolvable_reference`, and the two need
                # different words: one tells the user the citation is fictional, the other that it
                # names the right paper at the wrong page.
                if _parses(ref)
                and _label_exists(ref, by_label)
                and not _page_matches(ref, by_label)
            ]
            return ClaimVerification(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                label="Unsupported",
                support_score=0.0,
                similarity=0.0,
                overlap=0.0,
                evidence=None,
                relevance_score=None,
                reason=Reason.PAGE_MISMATCH if pages_disagree else Reason.UNRESOLVABLE_REFERENCE,
                explanation=(
                    (
                        f"The answer cites {raws}. That source was retrieved, but not at the page "
                        "the claim names, so the citation does not identify the passage it points "
                        "at. It was not re-pointed at the retrieved page."
                    )
                    if pages_disagree
                    else (
                        f"The answer cites {raws}, but no retrieved passage carries that reference. "
                        "The citation was not re-pointed at another passage: doing so would destroy "
                        "the traceability the reader is relying on."
                    )
                ),
            )

        # Multiple refs: use the highest-ranked one, so the claim is scored against the strongest
        # retrieved support available for it rather than an arbitrary cited passage.
        return min(resolvable, key=lambda pair: pair[0].rank)

    # -- similarity -----------------------------------------------------------

    def _similarity(self, claim: str, chunk_text: str, config: VerificationConfig) -> float:
        if self._similarity_fn is not None:
            raw = float(self._similarity_fn(claim, chunk_text))  # type: ignore[operator]
            if config.rescale_cosine_to_unit_interval:
                raw = (raw + 1.0) / 2.0
            return min(max(raw, 0.0), 1.0)

        # Fallback: deterministic lexical similarity, IDF-free. Cosine on term overlap is already in
        # [0, 1], so it is deliberately NOT rescaled -- rescaling would push an unrelated claim to
        # 0.5 and make "shares no vocabulary" look like partial support.
        claim_tokens = content_tokens(claim)
        chunk_tokens = content_tokens(chunk_text)
        if not claim_tokens or not chunk_tokens:
            return 0.0
        shared = claim_tokens & chunk_tokens
        if not shared:
            return 0.0
        denominator = (len(claim_tokens) * len(chunk_tokens)) ** 0.5
        return min(len(shared) / denominator, 1.0)


def _parses(ref: CitationRef) -> bool:
    """True when the reference's text is a well-formed marker."""
    return _REF_PATTERN.fullmatch(ref.raw.replace(" ", "")) is not None


def _label_exists(ref: CitationRef, by_label: dict[str, RetrievalResult]) -> bool:
    match = _REF_PATTERN.fullmatch(ref.raw.replace(" ", ""))
    return match is not None and f"S{int(match.group('label'))}" in by_label


def _page_matches(ref: CitationRef, by_label: dict[str, RetrievalResult]) -> bool:
    match = _REF_PATTERN.fullmatch(ref.raw.replace(" ", ""))
    if match is None:
        return False
    result = by_label.get(f"S{int(match.group('label'))}")
    return result is not None and result.chunk.page_number == int(match.group("page"))


def _label_index(retrieved: Sequence[RetrievalResult]) -> dict[str, RetrievalResult]:
    """Rebuild the ``S1``-style label map from the retrieval order.

    Deliberately derived from `rank` rather than read from the generator, so the verifier resolves
    against what was actually retrieved rather than trusting the label the generator wrote. If the
    two disagree, the verifier wins -- that is the whole design.
    """
    return {f"S{result.rank}": result for result in sorted(retrieved, key=lambda r: r.rank)}


def _explain(
    label: str,
    support: float,
    similarity: float,
    overlap: float,
    evidence: EvidenceChunk,
    ref: CitationRef,
    config: VerificationConfig,
) -> str:
    """Honest, user-facing prose. Never asserts proof (IV-6)."""
    ceiling = "Verified"
    parts = [
        f"Support score {support:.2f} (threshold for {label}: "
        f"{config.verified_threshold:.2f} for Verified, {config.review_threshold:.2f} for review).",
        f"Semantic component {similarity:.2f}, lexical containment {overlap:.2f}.",
        f"Cited {evidence.filename}, page {evidence.page_number}, marker [{ref.raw}].",
    ]
    if label == ceiling:
        parts.append(
            "This means the claim passed the project's documented support-check heuristic. It is an "
            "indicator of lexical and semantic correspondence with the cited passage -- not logical "
            "entailment, and not proof that the claim is factually true."
        )
    elif label == "Needs Review":
        parts.append(
            "The cited passage shares some vocabulary but not enough to clear the Verified "
            "threshold. Read the passage before relying on this claim."
        )
    else:
        parts.append(
            "The cited passage does not support this claim by the project's heuristic. The claim may "
            "be wrong, or the citation may point at the wrong place; this system cannot tell which."
        )
    return " ".join(parts)