"""Typed data contracts for the whole pipeline.

Every field name in this module is authoritative and is quoted verbatim by
docs/08_DATA_MODELS_AND_API_CONTRACTS.md. Renaming a field here is a contract
change and needs an ADR plus a tracker entry, not a quiet edit.

The two identity helpers (``compute_source_id`` / ``compute_chunk_id``) live here
rather than in ``pdf_ingestion`` or ``chunking`` on purpose: an ID scheme that is
implemented twice is an ID scheme that will eventually disagree with itself, and a
dangling ID means a citation that points nowhere. One implementation, one place.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "Reason",
    "USER_MESSAGES",
    "EXTRACTORS",
    "LABELS",
    "VERIFICATION_LABELS",
    "GENERATORS",
    "ResourceLimits",
    "DocumentPage",
    "DocumentSummary",
    "IngestFailure",
    "IndexReport",
    "IndexStats",
    "EvidenceChunk",
    "ChunkConfig",
    "RetrievalResult",
    "VerificationConfig",
    "CitationRef",
    "Claim",
    "GeneratedAnswer",
    "ClaimVerification",
    "VerificationSummary",
    "CoverageReport",
    "AbstentionConfig",
    "Correction",
    "CorrectionPlan",
    "QueryMetrics",
    "AnswerResponse",
    "PipelineConfig",
    "compute_source_id",
    "compute_chunk_id",
]


class Reason:
    """Stable machine-readable failure and verification codes.

    Defined as plain string constants rather than an ``Enum`` so that the values
    survive JSON export and Streamlit rendering unchanged. UI, tests and the
    report all match on these codes -- never on human-readable message text.
    """

    # Ingestion
    FILE_NOT_FOUND = "file_not_found"
    UNSUPPORTED_EXTENSION = "unsupported_extension"
    EMPTY_FILE = "empty_file"
    ENCRYPTED_PDF = "encrypted_pdf"
    CORRUPT_PDF = "corrupt_pdf"
    SCANNED_PDF = "scanned_pdf"
    TOO_MANY_PAGES = "too_many_pages"
    TOO_LARGE = "too_large"
    EMPTY_INDEX = "empty_index"
    ZERO_CHUNKS = "zero_chunks"

    # Verification (defined here so every module has one vocabulary; used from Phase 4)
    SUPPORTED = "supported"
    WEAK_SUPPORT = "weak_support"
    NO_SUPPORT = "no_support"
    UNRESOLVABLE_REFERENCE = "unresolvable_reference"
    PAGE_MISMATCH = "page_mismatch"
    MALFORMED_MARKER = "malformed_marker"
    NO_MARKER = "no_marker"
    NUMERIC_MISMATCH = "numeric_mismatch"
    CONTRADICTION_DETECTED = "contradiction_detected"


USER_MESSAGES: dict[str, str] = {
    Reason.FILE_NOT_FOUND: "That file could not be found.",
    Reason.UNSUPPORTED_EXTENSION: "Only PDF files are supported.",
    Reason.EMPTY_FILE: "That file is empty.",
    Reason.ENCRYPTED_PDF: (
        "Password-protected PDFs are not supported. Remove the password and upload "
        "the file again."
    ),
    Reason.CORRUPT_PDF: "That PDF could not be parsed.",
    Reason.SCANNED_PDF: (
        "No extractable text was found. This looks like a scanned or image-only PDF. "
        "OCR would be required to index it, and OCR is out of scope for this project."
    ),
    Reason.TOO_MANY_PAGES: "That document exceeds the configured page limit.",
    Reason.TOO_LARGE: "That file exceeds the configured size limit.",
    Reason.EMPTY_INDEX: "No usable text was found in any uploaded document.",
    Reason.ZERO_CHUNKS: "Chunking produced no chunks.",
}

EXTRACTORS: frozenset[str] = frozenset({"pypdf", "pdfplumber", "none"})
LABELS: frozenset[str] = frozenset({"indexed", "failed"})

# The only three outcomes the system may report. Fixed here, not chosen at runtime, so that a
# label like "hallucinated" cannot appear from anywhere: Stage 1 used that word and Stage 2
# replaced it, because "hallucinated" is an interpretation requiring evaluation, not a system
# output. See ADR-0006 and risk R-17.
VERIFICATION_LABELS: tuple[str, str, str] = ("Verified", "Needs Review", "Unsupported")

# Answer generators the pipeline knows how to build.
#
# `openrouter` is the optional hosted profile. It is listed last deliberately: the default and the
# test profile are both local, so a fresh clone reproduces its numbers with no key and no network.
# A remote model is an *option*, never a dependency -- see ADR-0016.
GENERATORS: tuple[str, ...] = ("extractive", "flan-t5-small", "openrouter")

# The hosted generator's default model.
#
# **Chosen from the live OpenRouter catalogue rather than from memory, because the catalogue turns
# over.** Checked against `https://openrouter.ai/api/v1/models`: 458 models, of which **15** carry
# the `:free` suffix and price at exactly `{"prompt": "0", "completion": "0"}`.
#
# The commonly-published free IDs no longer exist. At the time of writing there are **zero** free
# models from meta-llama, qwen, deepseek, mistralai or openai, so any documentation naming one of
# them as a default would ship a broken default.
#
# **Why a list and not one id -- a measured decision.** A live call with a real key, 2026-10-11:
# `google/gemma-4-26b-a4b-it:free` returned HTTP 429 five times in a row (~48 s of backoff) and
# never produced an answer, twice; `google/gemma-4-31b-it:free` returned 429 immediately;
# `thinkingmachines/*` returned **HTTP 403** (not available to this account);
# `nvidia/nemotron-3.5-lightning:free`, `dots-studio/*` and `apodex/*` returned HTTP 200 with a
# **null** content field, which is a different failure again; `poolside/laguna-s-2.1:free`
# answered correctly and quickly. So "present in the catalogue", "permitted for this account",
# "actually returns text" and "not rate-limited" are four different properties, and only the last
# one is discovered by calling.
#
# The generator therefore tries these in order and moves on when one fails. That is not a
# convenience: with a single hardcoded id the feature degrades to extractive whenever that one
# endpoint is busy, which is most of the time on a free tier.
DEFAULT_REMOTE_MODEL = "poolside/laguna-s-2.1:free"

# Ordered by observed reliability, not by quality. All are free-tier and all may disappear.
REMOTE_FALLBACK_MODELS: tuple[str, ...] = (
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-31b-it:free",
    "dots-studio/dots-3-note-preview:free",
)


@dataclass(frozen=True)
class ResourceLimits:
    """Hard bounds on untrusted input.

    These exist so that a hostile file -- a decompression bomb, a 5,000 page
    document, a multi-gigabyte upload -- is refused before it can exhaust memory,
    not after. ``total_page_warning`` is a soft ceiling on the *collection*, not a
    limit: exceeding it is worth telling the user about, never worth refusing them.
    """

    max_upload_mb: int = 50
    max_pages_per_document: int = 200
    total_page_warning: int = 1000

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def __post_init__(self) -> None:
        if self.max_upload_mb <= 0:
            raise ValueError("max_upload_mb must be positive")
        if self.max_pages_per_document <= 0:
            raise ValueError("max_pages_per_document must be positive")
        if self.total_page_warning <= 0:
            raise ValueError("total_page_warning must be positive")


@dataclass(frozen=True)
class DocumentPage:
    """One extracted page of one document."""

    source_id: str
    filename: str
    display_name: str
    page_number: int
    text: str
    extractor: str
    warnings: tuple[str, ...] = ()
    # Derived, never supplied: a caller cannot make char_count disagree with text.
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id must not be empty")
        if self.page_number < 1:
            raise ValueError("page_number is 1-based and must be >= 1")
        if self.extractor not in EXTRACTORS:
            raise ValueError(f"unknown extractor: {self.extractor!r}")
        object.__setattr__(self, "char_count", len(self.text))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IngestFailure:
    """A file that did not make it into the index, and why.

    Never swallowed. A traceability tool that quietly drops a file teaches the
    user to trust a corpus that is not there.
    """

    filename: str
    reason: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentSummary:
    """One row of the document library."""

    source_id: str
    display_name: str
    page_count: int
    chunk_count: int
    status: str
    engine: str

    def __post_init__(self) -> None:
        if self.status not in LABELS:
            raise ValueError(f"unknown status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndexReport:
    """Result of ``pipeline.index()`` -- the UI's only view of what is indexed."""

    documents: tuple[DocumentSummary, ...]
    total_pages: int
    total_chunks: int
    backend: str
    store: str
    persist_path: str | None
    elapsed_seconds: float
    warnings: tuple[str, ...] = ()
    failures: tuple[IngestFailure, ...] = ()

    def is_empty(self) -> bool:
        return self.total_chunks == 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndexStats:
    """Live counts for the UI. Measured from the index, never asserted in the UI."""

    document_count: int
    total_pages: int
    total_chunks: int
    backend: str
    store: str
    persist_path: str | None
    documents: tuple[DocumentSummary, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceChunk:
    """The unit of retrieval and of verification.

    ``citation_label`` is display sugar. Identity is ``chunk_id``; a label is
    reassigned per answer and must never be parsed to recover identity.
    """

    chunk_id: str
    source_id: str
    filename: str
    page_number: int
    chunk_index_in_page: int
    text: str
    citation_label: str = ""
    # Set by ingestion for a bibliography page. The chunk stays fully searchable and inspectable --
    # it is still evidence, and a question like "what does reference [3] say?" must still be
    # answerable. It is demoted, never hidden, because deleting it would make a citation
    # unresolvable. Defaults to False so a caller constructing a chunk directly is unaffected.
    is_reference_page: bool = False
    word_count: int = field(init=False)

    def __post_init__(self) -> None:
        if not self.chunk_id:
            raise ValueError("chunk_id must not be empty")
        if self.page_number < 1:
            raise ValueError("page_number is 1-based and must be >= 1")
        if self.chunk_index_in_page < 0:
            raise ValueError("chunk_index_in_page is 0-based and must be >= 0")
        object.__setattr__(self, "word_count", len(self.text.split()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChunkConfig:
    """Sentence-aware chunking parameters.

    ``chunk_words`` is a target, not a maximum: a chunk is closed at the last
    sentence boundary at or after the target, so it may overshoot slightly. What
    is exact is the overlap, because that is what keeps a definition from being
    split across a boundary.
    """

    chunk_words: int = 180
    overlap_words: int = 30
    respect_sentences: bool = True
    min_chunk_words: int = 20

    def __post_init__(self) -> None:
        if self.chunk_words <= 0:
            raise ValueError("chunk_words must be positive")
        if self.overlap_words < 0:
            raise ValueError("overlap_words must be non-negative")
        if self.overlap_words >= self.chunk_words:
            raise ValueError(
                f"overlap_words ({self.overlap_words}) must be less than chunk_words "
                f"({self.chunk_words}); an equal or larger overlap cannot advance"
            )
        if self.min_chunk_words <= 0:
            raise ValueError("min_chunk_words must be positive")
        if self.min_chunk_words > self.chunk_words:
            raise ValueError("min_chunk_words must not exceed chunk_words")

    @property
    def advance_words(self) -> int:
        """How far the window moves per chunk. Always > 0, or we would loop forever."""
        return self.chunk_words - self.overlap_words


@dataclass(frozen=True)
class RetrievalResult:
    """One retrieved passage and how relevant it is to the question.

    The single most load-bearing type in Phase 3, because it is the one place
    where a score could quietly start meaning the wrong thing.

    ``relevance_score`` answers exactly one question: *is this passage about what
    was asked?* It is a **retrieval** quantity. It is never claim support, never
    averaged with support, and there is deliberately no ``support_score`` field on
    this type -- invariant IR-5, guarded by test CT-08. If one is ever added, the
    ADR process applies.
    """

    rank: int
    chunk: EvidenceChunk
    relevance_score: float
    backend: str

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError("rank is 1-based and must be >= 1")
        # A store that normalises correctly cannot produce a score outside [0, 1].
        # The tolerance absorbs float noise, not real out-of-range values.
        if not -1e-9 <= self.relevance_score <= 1.0 + 1e-9:
            raise ValueError(
                f"relevance_score must be normalised to [0, 1]; got {self.relevance_score!r}"
            )
        object.__setattr__(self, "relevance_score", min(max(self.relevance_score, 0.0), 1.0))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationConfig:
    """Every knob the verifier has, in one place.

    Nothing in `verifier.py` may contain a numeric threshold literal. That is not style: a threshold
    buried inside a scoring function cannot be calibrated, cannot be reported, and cannot be argued
    about at a viva. Every value here is configuration a labeller can move.
    """

    similarity_weight: float = 0.7
    overlap_weight: float = 0.3
    # Calibrated 2026-10-08 against the 24 hand-labelled cases in
    # tests/data/eval_cases.jsonl, by sweeping [0.30, 0.90] in steps of 0.01 and taking the
    # correctness-first operating point: the highest F1 whose false-Verified rate is 0.
    #
    # The previous default of 0.62 was an unmeasured guess inherited from Stage 2. At 0.62 the
    # measured false-Verified rate was 0.125 (1 of 8) -- precisely the harm this project exists to
    # prevent. At 0.63 that case scores exactly 0.630 and drops out, giving precision 1.00 at recall
    # 0.70.
    #
    # Read the numbers as what they are: 24 self-authored cases from one 15-page report. They
    # justify this operating point; they do not establish it as correct in general. See
    # docs/15_PROGRESS_TRACKER.md section 7d and risk R-10.
    verified_threshold: float = 0.63
    review_threshold: float = 0.40
    check_numbers: bool = True
    check_contradiction: bool = True
    min_numeric_tokens: int = 2
    rescale_cosine_to_unit_interval: bool = True

    def __post_init__(self) -> None:
        total = self.similarity_weight + self.overlap_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"similarity_weight + overlap_weight must equal 1.0; got {total!r}. A support "
                "score is a weighted mean of exactly two components, nothing else."
            )
        if not 0.0 <= self.review_threshold < self.verified_threshold <= 1.0:
            raise ValueError(
                "thresholds must satisfy 0 <= review_threshold < verified_threshold <= 1.0; "
                f"got review={self.review_threshold!r}, verified={self.verified_threshold!r}"
            )
        if self.min_numeric_tokens < 1:
            raise ValueError("min_numeric_tokens must be at least 1")

    def score(self, similarity: float, overlap: float) -> float:
        """The Stage 2 formula. The single place the weighting exists."""
        return self.similarity_weight * similarity + self.overlap_weight * overlap


@dataclass(frozen=True)
class CoverageReport:
    """How much of a question's vocabulary the retrieved passages actually contain.

    This is the *retrieval-side* answer to "do these passages talk about what was
    asked?", and it is deliberately **not** `relevance_score`. The two disagree, and the
    disagreement is the finding that produced this type: on the 48-case labelled set
    the top-1 cosine of an answerable question overlaps the top-1 cosine of an
    unanswerable one, so no threshold on that score can separate them. Coverage
    separates them cleanly. See `pipeline.query_coverage` for the measurement.

    Kept as a report rather than a bare float so the UI and the evaluation harness can
    show *which* terms matched and which did not. A number the user cannot interrogate
    is a number they have to trust, which is the thing this project is against.
    """

    covered: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def terms(self) -> int:
        return len(self.covered) + len(self.missing)

    @property
    def value(self) -> float:
        """Fraction of the question's content terms present. `1.0` when the question
        has no content terms at all, because absence of signal is not evidence of
        absence of an answer.

        Callers must handle the no-terms case explicitly rather than trusting this
        value: `1.0` would sail through any gate, which is the intended
        do-not-abstain behaviour but is a decision, not a measurement.
        """
        if not self.terms:
            return 1.0
        return len(self.covered) / self.terms


@dataclass(frozen=True)
class AbstentionConfig:
    """When the pipeline refuses to answer rather than quoting weak evidence.

    Separated from `VerificationConfig` because the two answer different questions.
    Verification asks *does this cited passage support this claim*, and it runs after
    an answer exists. This asks *was there anything worth answering from*, and it runs
    before generation, so a claim is never manufactured only to be labelled Unsupported
    afterwards.

    **`min_query_coverage` is calibrated on labelled data, not chosen.** The sweep over
    [tests/data/abstention_cases.jsonl](../tests/data/abstention_cases.jsonl) is in
    [docs/10_EVALUATION_METRICS.md](docs/10_EVALUATION_METRICS.md). 24 answerable and
    24 unanswerable questions give a clean gap: answerable coverage bottoms out well
    above the floor and unanswerable coverage tops out well below it. The floor sits
    inside that gap and is never derived from a single example.
    """

    # 0.50 sits inside the measured gap between the answerable minimum (0.667) and the
    # unanswerable maximum (0.250) for `retrieved` scope. Rounded from the mid-gap of
    # 0.458; the margin absorbs a labeller disagreeing with one borderline label.
    #
    # **0.65 scores marginally better on the labelled set and is still the wrong choice.**
    # The sweep gives floor 0.65 a correct-abstention rate of 0.792 at the same 0.000
    # false-abstention rate, so it dominates 0.50 on the headline numbers. Its margin to
    # the nearest answerable case is 0.017, however: one labelled question sits at 0.667,
    # and re-phrasing it, or a chunk-boundary change, would push it under. At 0.50 that
    # margin is 0.167 on the answerable side and 0.250 on the unanswerable side.
    #
    # Picking 0.65 would be fitting the threshold to the set that justifies it, which is
    # the exact failure this project's own evidence rules exist to prevent. Recorded in
    # docs/10_EVALUATION_METRICS.md so the decision is auditable rather than invisible.
    min_query_coverage: float = 0.50
    # "retrieved" pools every chunk the pipeline retrieved, which is what the generator
    # is actually allowed to quote. "top" scores only the highest-ranked chunk, which is
    # stricter and misses answers that live at rank 3.
    coverage_scope: str = "retrieved"
    enabled: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_query_coverage <= 1.0:
            raise ValueError(
                f"min_query_coverage must be in [0, 1]; got {self.min_query_coverage!r}"
            )
        if self.coverage_scope not in {"retrieved", "top"}:
            raise ValueError(
                f"unknown coverage_scope: {self.coverage_scope!r}; expected 'retrieved' or 'top'"
            )


@dataclass(frozen=True)
class CitationRef:
    """One `[S?, p.?]` reference as written in an answer.

    ``resolved`` is ``False`` when no retrieved chunk matches. A reference that does not resolve is
    reported, never repaired -- see ADR-0008.
    """

    source_id: str | None
    page_number: int | None
    raw: str
    resolved: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Claim:
    """One sentence of an answer, plus the markers it cites.

    ``text`` has markers stripped: `[S1, p.5]` is not part of the claim, and scoring it as though it
    were would give every claim the same extra tokens and inflate every score.
    """

    claim_id: str
    text: str
    markers: tuple[CitationRef, ...]
    position: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeneratedAnswer:
    """An answer and the claims it is made of.

    ``degraded`` must be surfaced in the UI. A degraded run that looks identical to a full run is
    dishonest -- see Architecture section 6.
    """

    text: str
    claims: tuple[Claim, ...]
    generator: str
    degraded: bool = False
    abstained: bool = False
    abstention_reason: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # `notes=( "a" "b" )` reads as a tuple but is a plain string, and a string iterates
        # character by character. Every consumer here joins or scans `notes`, so the result is
        # a UI panel of single letters that looks like corrupted text rather than an error.
        # Coerced here so a caller who writes `notes="..."` gets one note instead of 200.
        if isinstance(self.notes, str):
            object.__setattr__(self, "notes", (self.notes,))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimVerification:
    """The verdict on one claim, with every number that produced it.

    ``relevance_score`` is copied here **for display only** and is never an input to
    ``support_score`` (IV-7). It answers a different question -- "is this passage about what was
    asked?" -- and showing it in the same panel as the support score is deliberate, because the user
    needs both and the naming is what stops them reading them as one number.
    """

    claim_id: str
    claim_text: str
    label: str
    support_score: float
    similarity: float
    overlap: float
    evidence: EvidenceChunk | None
    relevance_score: float | None
    reason: str
    explanation: str

    def __post_init__(self) -> None:
        if self.label not in VERIFICATION_LABELS:
            raise ValueError(
                f"unknown verification label {self.label!r}; expected one of {VERIFICATION_LABELS}"
            )
        if not self.reason:
            raise ValueError("a ClaimVerification must carry a reason code (IV-5)")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["label"] = self.label
        return payload


@dataclass(frozen=True)
class VerificationSummary:
    """Counts across an answer. Deliberately not an average."""

    verified: int
    needs_review: int
    unsupported: int
    uncited: int
    unresolved_refs: int
    worst_support: float | None
    abstained: bool

    @property
    def headline(self) -> str:
        """An honest one-line summary.

        Counts and the worst score, never a mean. Averaging is how one unsupported claim hides behind
        three supported ones, and a single averaged percentage is exactly the number that looks
        authoritative and means nothing.
        """
        if self.abstained:
            return "No answer was produced: the retrieved evidence was insufficient."
        if self.verified + self.needs_review + self.unsupported == 0:
            return "No verifiable claims were produced."
        parts = [
            f"{self.verified} Verified",
            f"{self.needs_review} Needs Review",
            f"{self.unsupported} Unsupported",
        ]
        text = "; ".join(parts)
        if self.uncited:
            text += f"; {self.uncited} claim(s) carried no citation"
        if self.unresolved_refs:
            text += f"; {self.unresolved_refs} citation(s) did not resolve"
        if self.worst_support is not None:
            text += f". Weakest claim support: {self.worst_support:.2f}"
        return text

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Correction:
    """One thing wrong with a claim's citation, and what to do about it.

    This is the project's answer to "the citation looks wrong -- what now?". A verification label
    says *what the system found*; a correction says *what the author should change*, in a form they
    can act on without reading this source code.

    Three fields, each doing a distinct job:

    * ``action`` is a stable code, so the UI can pick an icon and a test can assert a category
      without matching on prose.
    * ``suggestion`` is the human instruction. It names the specific page and the specific term
      rather than saying "improve your citation", because advice that cannot be acted on is the
      same as no advice.
    * ``repair_prompt`` is a ready-to-paste prompt for a general-purpose assistant, so the user can
      get a drafted rewrite instead of editing prose alone. It is **derived only from material this
      system already retrieved** -- never from the source document as a whole -- so the prompt
      cannot smuggle in context the user has not seen.
    """

    claim_id: str
    claim_text: str
    action: str
    suggestion: str
    repair_prompt: str
    evidence_page: int | None = None
    current_marker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# The actions a `Correction` may recommend. A closed vocabulary, like the verification labels, so
# the UI cannot render an action nobody designed for.
CORRECTION_ACTIONS: tuple[str, ...] = (
    "add_citation",
    "fix_page_number",
    "replace_fabricated_citation",
    "reword_to_match_source",
    "remove_unsupported_claim",
    "resolve_marker_syntax",
    "none",
)


@dataclass(frozen=True)
class CorrectionPlan:
    """Every correction for one answer, plus a pasteable prompt covering all of them.

    Kept separate from `Correction` so the UI can show "3 issues found" without walking the list,
    and so an answer with nothing wrong has one obvious empty representation.
    """

    corrections: tuple[Correction, ...]
    summary_prompt: str

    def __iter__(self):
        """Iterating a plan yields its corrections.

        Present so every consumer can write ``for correction in plan`` rather than reaching through
        to ``plan.corrections``. Frozen dataclass fields are plain tuples and are not iterable
        themselves, and a wrapper type that cannot be walked is a trap at the call site.
        """
        return iter(self.corrections)

    def __len__(self) -> int:
        return len(self.corrections)

    def __bool__(self) -> bool:
        return bool(self.corrections)

    @property
    def is_empty(self) -> bool:
        return not self.corrections

    @property
    def actionable_count(self) -> int:
        """Corrections that are not the placeholder ``none`` entry."""
        return sum(1 for correction in self.corrections if correction.action != "none")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryMetrics:
    """Measured timings for one query. Never estimated, never shown as a promise."""

    embed_ms: float
    retrieve_ms: float
    generate_ms: float
    verify_ms: float
    total_ms: float
    backend: str
    store: str
    generator: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnswerResponse:
    """The single object the UI renders. Nothing else.

    ``corrections`` is what turns a label into an action: the verifier says a claim's page number
    is wrong, and the advisor says which page, and the repair prompt says how to rewrite the
    sentence. It is computed from ``verifications`` by a pure function, so it cannot disagree with
    the labels it was derived from.
    """

    question: str
    answer: GeneratedAnswer
    retrieved: tuple[RetrievalResult, ...]
    verifications: tuple[ClaimVerification, ...]
    summary: VerificationSummary
    metrics: QueryMetrics
    warnings: tuple[str, ...] = ()
    corrections: CorrectionPlan = CorrectionPlan(corrections=(), summary_prompt="")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PipelineConfig:
    """Everything the orchestrator needs, in one immutable object.

    The profile differs by field value, never by a different pipeline: that is what makes the
    offline fallback testable rather than aspirational (ADR-0005).
    """

    chunk: ChunkConfig = ChunkConfig()
    top_k: int = 5
    embedding_backend: str = "tfidf"
    store: str = "memory"
    generator: str = "extractive"
    persist_path: Path | None = None
    verification: VerificationConfig = VerificationConfig()
    abstention: AbstentionConfig = AbstentionConfig()
    limits: ResourceLimits = ResourceLimits()

    def __post_init__(self) -> None:
        if self.top_k < 1:
            raise ValueError("top_k must be at least 1")
        if self.embedding_backend not in {"tfidf", "minilm"}:
            raise ValueError(f"unknown embedding_backend: {self.embedding_backend!r}")
        if self.store not in {"memory", "chroma"}:
            raise ValueError(f"unknown store: {self.store!r}")
        if self.generator not in GENERATORS:
            raise ValueError(f"unknown generator: {self.generator!r}")
        if self.store == "chroma" and self.persist_path is None:
            raise ValueError("the chroma store requires a persist_path")

    @property
    def is_semantic(self) -> bool:
        return self.embedding_backend == "minilm"


_WS_RUN = re.compile(r"\s+")


def _normalise_filename_for_id(filename: str) -> str:
    """Fold a filename to a form that does not vary with path or incidental spacing.

    Two uploads of the same document arriving from different folders must produce
    the same ``source_id``, otherwise re-indexing would orphan every existing
    reference.
    """
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    return _WS_RUN.sub(" ", base).strip().lower()


def compute_source_id(filename: str, size_bytes: int, page_count: int) -> str:
    """Content-derived document identity.

    Uses filename + size + page count rather than the absolute path: a path would
    make the ID machine-specific, and a pure hash of the bytes would make every
    re-export a new document. The rare same-name/same-size/same-page-count
    collision is tracked as R-07.
    """
    key = f"{_normalise_filename_for_id(filename)}|{size_bytes}|{page_count}"
    return "doc_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def compute_chunk_id(source_id: str, page_number: int, chunk_index_in_page: int) -> str:
    """Content-derived chunk identity, stable across runs and across re-indexing."""
    key = f"{source_id}|{page_number}|{chunk_index_in_page}"
    return "chk_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]