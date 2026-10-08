# 08 — Data Models & API Contracts

**Status:** Phase 1 design · Last updated 2026-10-08
**Related:** [Architecture](04_SYSTEM_ARCHITECTURE.md) · [Requirements](01_REQUIREMENTS.md) · [Testing](09_TESTING_STRATEGY.md)

---

## 1. Conventions

- Python `dataclasses`, frozen where the object should not mutate after construction.
- All fields typed. No `Any` in a public contract.
- Field names here are authoritative. Code and docs reference these exact names.
- Optional fields are `X | None = None`, never a sentinel like `0` or `""`.
- Every contract object has a `to_dict()` for logging, JSON export and the evidence tracker.

### 1.1 Phase 2–3 refinements to the sketches below

The field *names* above are unchanged. Two implementation decisions were made in Phase 2 that the
sketches did not anticipate, recorded here so the doc and the code do not drift:

1. **`char_count` and `word_count` are `field(init=False)`**, computed in `__post_init__` rather
   than passed in. A caller must not be able to build a `DocumentPage` whose `char_count` disagrees
   with its `text` — that inconsistency would quietly corrupt every downstream word count.
2. **The reason codes in §6 are string constants on a `Reason` class**, not an `Enum`, so the
   values survive JSON export and Streamlit rendering unchanged. `USER_MESSAGES` maps each ingestion
   code to the exact user-facing sentence, so no module has to re-word a message.
3. **The ID helpers (§4) live in `models.py`**, not in `pdf_ingestion` or `chunking`. An ID scheme
   implemented twice eventually disagrees with itself, and a wrong ID is a citation pointing
   nowhere. Decision D-13 in the [progress tracker](15_PROGRESS_TRACKER.md#5-decisions-log).
4. **`PipelineConfig` (§10.4) is currently missing `verification` and `generator`.** They are not
   stubbed, because no code path should be able to read a threshold that does not exist yet. They
   arrive with the verifier in Phase 4 — decision D-16.
5. **`set_similarity` takes a scorer name.** §7.2's sketch shows `VectorStore` without it; the
   implementation requires `(fn, name)` so that `RetrievalResult.backend` can name the *embedding*
   backend that produced a score. "0.72 from TF-IDF" is a meaningful claim; "0.72 from memory" says
   nothing. Decision D-17.
6. **`IndexStats` (§10.3 returns it but §2 does not define it).** Added in Phase 3:
   `document_count`, `total_pages`, `total_chunks`, `backend`, `store`, `persist_path`,
   `documents: tuple[DocumentSummary, ...]`. Every field is measured from the live index.

### 1.2 Two additions Phase 3 had to make

Both are degradation-path state, surfaced in the UI rather than hidden, per
[Architecture §6](04_SYSTEM_ARCHITECTURE.md#6-failure-modes-and-degradation).

| Property on `ResearchPipeline` | Meaning |
|---|---|
| `degraded_reason: str \| None` | The configured profile is not the one running, and why. `None` in every normal run. |
| `stale_chunks: int` | Chunks embedded by a *previous* backend, so the current one cannot score them. Zero unless a mid-session degradation occurred. They are **not** returned by retrieval; a full rebuild is the only fix. |
| `restored_chunks: int` | Chunks recovered from a persisted index at startup rather than re-read from PDFs. The observable behind EC-15. |

The `stale_chunks` case is worth stating plainly because it is easy to get wrong: a TF-IDF query
vector cannot meaningfully score MiniLM vectors. Silently returning those chunks would produce
relevance numbers that look real and mean nothing.

---

## 2. Ingestion contracts

### 2.1 `DocumentPage`

One extracted page of one document. Produced by `pdf_ingestion`, consumed by `chunking`.

```python
@dataclass(frozen=True)
class DocumentPage:
    source_id: str            # stable document identifier, see §4
    filename: str             # original upload name, unmodified
    display_name: str         # sanitised name for UI display, see §5
    page_number: int          # 1-based, matches the reader's page
    text: str                 # extracted text, whitespace-normalised
    char_count: int
    extractor: str            # "pypdf" | "pdfplumber" | "none"
    warnings: tuple[str, ...] = ()
```

**Invariants**

| # | Invariant |
|---|---|
| IP-1 | `page_number >= 1` and is sequential with no gaps within a document |
| IP-2 | `source_id` is identical for every page of the same document, and **stable across runs** |
| IP-3 | `filename` is never rewritten; only `display_name` is sanitised |
| IP-4 | An empty `text` is allowed on a single page but never for an entire document |

### 2.2 `IndexReport`

Result of `pipeline.index()`. The UI's only source of truth for "what is in the index".

```python
@dataclass(frozen=True)
class IndexReport:
    documents: tuple[DocumentSummary, ...]
    total_pages: int
    total_chunks: int
    backend: str                    # "tfidf" | "minilm"
    store: str                      # "memory" | "chroma"
    persist_path: str | None
    elapsed_seconds: float
    warnings: tuple[str, ...] = ()
    failures: tuple[IngestFailure, ...] = ()

    def is_empty(self) -> bool: ...
```

### 2.3 `DocumentSummary` and `IngestFailure`

```python
@dataclass(frozen=True)
class DocumentSummary:
    source_id: str
    display_name: str
    page_count: int
    chunk_count: int
    status: str                    # "indexed" | "failed"
    engine: str

@dataclass(frozen=True)
class IngestFailure:
    filename: str
    reason: str                    # machine-readable, see §6
    message: str                   # human-readable, safe to show the user
```

`failures` is **never** swallowed. A file that fails to index appears as `failed` in the library with
its real reason. Silent drops are how users lose trust in a traceability tool.

---

## 3. Chunking contract

### 3.1 `EvidenceChunk`

The unit of retrieval and of verification. This is the most important type in the project.

```python
@dataclass(frozen=True)
class EvidenceChunk:
    chunk_id: str                  # stable, deterministic, see §4
    source_id: str
    filename: str
    page_number: int               # real PDF page, 1-based
    chunk_index_in_page: int       # 0-based, for debugging and stable tie-breaks
    text: str
    word_count: int
    # citation display only — not an identity
    citation_label: str            # e.g. "S1, p.5"
```

**Invariants**

| # | Invariant |
|---|---|
| IC-1 | `chunk_id` is deterministic: same PDF + same config ⇒ same ID |
| IC-2 | `page_number` is the real page a human will see when opening the PDF |
| IC-3 | `citation_label` is presentational. **Identity comes from `chunk_id`.** Never parse a label to recover identity |
| IC-4 | Consecutive chunks in a page overlap by exactly the configured number of words |
| IC-5 | A chunk never spans two pages |

IC-5 is deliberate: cross-page chunks make the page number in a citation ambiguous, which would break
the product's central promise. A sentence spanning a page break is kept whole in the earlier page's
chunk and noted as a warning.

### 3.2 `ChunkConfig`

```python
@dataclass(frozen=True)
class ChunkConfig:
    chunk_words: int = 180
    overlap_words: int = 30
    respect_sentences: bool = True
    min_chunk_words: int = 20       # below this, merge with the previous chunk
```

**Validation (FR-13, EC-07):** `chunk_words > 0`, `0 <= overlap_words < chunk_words`, else
`ValueError`. `overlap_words == chunk_words` must raise — that configuration cannot advance.

---

## 4. Identity and ID scheme

Fragile IDs silently break citations, which is the worst failure this project can have. So IDs are
**content-derived, not positional**.

```text
source_id = "doc_" + sha1(normalised_filename + "|" + file_size_bytes + "|" + page_count)[:12]
chunk_id  = "chk_" + sha1(source_id + "|" + page_number + "|" + str(chunk_index_in_page))[:12]
```

| Property | Guaranteed |
|---|---|
| Deterministic | Same file ⇒ same IDs on every machine and every run |
| Stable across re-index | Re-indexing the same file produces the same IDs, so old references do not dangle |
| Distinct across documents | Two files with the same name and size and page count collide — acceptably rare, and detectable; see risk R-07 |
| Not a raw path | The absolute path never leaks into an ID or a UI element |
| Not `id()` / index-based | No process-dependent values anywhere |

`citation_label` (`"S1, p.5"`) is assigned at *answer* time from the retrieved set, in rank order,
and is purely for display. Stage 2's example format is `[S1, p.5]` — the label is placed inside square
brackets by the marker regex.

## 5. Sanitised display names (SEC-01)

`display_name` is derived, never stored from untrusted input:

```text
1. take os.path.basename(filename)          # strip any directory component
2. replace path separators and control characters with "_"
3. collapse whitespace runs to a single space
4. strip leading dots (defeats "..")
5. truncate to 120 characters, preserving a readable stem
6. if the result is empty or all punctuation → "unnamed-document.pdf"
```

The original `filename` is retained for the user's own recognition, but **only `display_name` is ever
rendered**, and it is still escaped at render time.

---

## 6. Reason codes

Failures and verification outcomes use stable machine-readable codes so the UI, the tests and the
report can all refer to the same thing. Never match on human-readable message text.

### 6.1 Ingestion

| Code | User message (paraphrase) |
|---|---|
| `file_not_found` | That file could not be found |
| `unsupported_extension` | Only PDF files are supported |
| `empty_file` | That file is empty |
| `encrypted_pdf` | Password-protected PDFs are not supported |
| `corrupt_pdf` | That PDF could not be parsed |
| `scanned_pdf` | No extractable text found — this looks scanned, and OCR is out of scope |
| `too_many_pages` | That document exceeds the configured page limit |
| `too_large` | That file exceeds the configured size limit |
| `empty_index` | No usable text was found in any uploaded document |
| `zero_chunks` | Chunking produced no chunks |

### 6.2 Verification

| Code | Meaning |
|---|---|
| `supported` | Passed the support check at the configured threshold |
| `weak_support` | Between thresholds ⇒ `Needs Review` |
| `no_support` | Below the review threshold ⇒ `Unsupported` |
| `unresolvable_reference` | The cited source was never retrieved |
| `page_mismatch` | The source was retrieved but not at the cited page |
| `malformed_marker` | The marker text could not be parsed |
| `no_marker` | A claim sentence carried no citation at all |
| `numeric_mismatch` | A number in the claim is absent from the cited passage |
| `contradiction_detected` | Polarity/negation disagreement with the cited passage |

Every `ClaimVerification` carries one of these. A verification result without a reason code is
incomplete and should fail its test.

---

## 7. Retrieval contract

### 7.1 `RetrievalResult`

```python
@dataclass(frozen=True)
class RetrievalResult:
    rank: int                      # 1-based, after sorting
    chunk: EvidenceChunk
    relevance_score: float         # [0, 1] — query vs chunk ONLY
    backend: str                   # which similarity produced it
```

**Invariants**

| # | Invariant |
|---|---|
| IR-1 | `relevance_score` means "how relevant is this passage to the question" — never claim support |
| IR-2 | `rank` is 1-based and contiguous from 1 |
| IR-3 | Results are sorted by `(-relevance_score, chunk_id)` — the `chunk_id` tie-break makes ordering deterministic |
| IR-4 | `len(results) == min(top_k, collection_size)` |
| IR-5 | No `support_score` field may appear in this type. If one is ever added, the ADR process applies |
| IR-6 | `backend` names the **embedding** backend that produced the score, not the store. Decision D-17 |

IR-5 is the mechanical guard against conflating the two scores. CT-08 asserts it three ways: the
field is absent from `__dataclass_fields__`, the attribute does not exist on an instance, and **no**
field name in the type contains the substring "support". Only the third survives someone re-adding a
differently-named version of the same mistake.

`__post_init__` also enforces `rank >= 1` and `0 <= relevance_score <= 1` (with a 1e-9 float
tolerance). A store that failed to normalise would fail here rather than displaying a score of 1.4.

### 7.2 Store protocol

```python
class VectorStore(Protocol):
    def add(self, chunks: Sequence[EvidenceChunk], vectors: object) -> None: ...
    def query(self, query_vector: object, top_k: int) -> list[RetrievalResult]: ...
    def count(self) -> int: ...
    def delete_document(self, source_id: str) -> int: ...
    def persist(self) -> None: ...
```

Implementations: `InMemoryVectorStore` (deterministic, test profile) and `ChromaVectorStore`
(persistent semantic profile). `top_k` clamping happens inside `query` so no caller can forget it.

**Phase 3 additions to the protocol.** Both stores also expose:

| Method / property | Why |
|---|---|
| `set_similarity(fn, scorer_name)` | Wiring, not part of querying. The store holds no opinion about cosine, TF-IDF or rescaling — it is handed the embedding backend's own function, which is what stops a store inventing a second, subtly different scoring rule. `scorer_name` populates `RetrievalResult.backend`. |
| `stored_texts()` → `list[str]` | **Chroma only.** Lets a restarted TF-IDF backend rebuild its vocabulary without re-reading the PDFs. The memory store has no reason to need it and does not implement it; the pipeline feature-detects it. |

`persist()` is a documented no-op in both. `PersistentClient` writes on every mutation, and the
in-memory store is deliberately not persistent. It stays in the protocol so one call site serves
both backends and a future store with an explicit flush has an obvious place to put it.

---

## 8. Generation contract

### 8.1 `GeneratedAnswer`

```python
@dataclass(frozen=True)
class GeneratedAnswer:
    text: str                                  # with markers inline
    claims: tuple[Claim, ...]
    generator: str                             # "extractive" | "flan-t5-small"
    degraded: bool = False                     # True when fallback is active
    abstained: bool = False
    abstention_reason: str | None = None
    notes: tuple[str, ...] = ()
```

`degraded=True` **must** be surfaced in the UI. A degraded run that looks identical to a full run is
dishonest — see [Architecture §6](04_SYSTEM_ARCHITECTURE.md#6-failure-modes-and-degradation).

### 8.2 `Claim`

A claim is one sentence of the answer plus its markers.

```python
@dataclass(frozen=True)
class Claim:
    claim_id: str                  # "clm_..." deterministic, from position
    text: str                      # sentence with markers stripped for scoring
    markers: tuple[CitationRef, ...]
    position: int                  # 0-based index in the answer
```

```python
@dataclass(frozen=True)
class CitationRef:
    source_id: str | None          # resolved, or None if unresolvable
    page_number: int | None
    raw: str                       # original marker text, e.g. "S1, p.5"
    resolved: bool
```

**Why markers are stripped before scoring:** the marker text `[S1, p.5]` is not part of the claim. If
it were included in the similarity input, every claim would share the marker tokens and inflate its
score — a subtle bug that would systematically over-report `Verified`.

### 8.3 Marker grammar

```text
marker      := "[" reference ("," reference)* "]"
reference   := "S" digits "," "p." digits        # e.g. S1, p.5
```

Strict regex, no fuzzy matching:

```regex
\[(?P<refs>S\d+\s*,\s*p\.\s*\d+(?:\s*;\s*S\d+\s*,\s*p\.\s*\d+)*)\]
```

- **Malformed markers are reported, not repaired.** `[S1 p5]` is `malformed_marker` ⇒
  `Unsupported`. We never guess the author's intent.
- Multiple refs in one bracket are supported: `[S1, p.5; S3, p.9]`.
- A claim with no marker is `no_marker` ⇒ cannot be `Verified`. An uncited factual claim is exactly
  the failure this project exists to catch.

### 8.4 Generator protocol

```python
class AnswerGenerator(Protocol):
    name: str
    def generate(
        self,
        question: str,
        evidence: Sequence[EvidenceChunk],
        max_sentences: int = 5,
    ) -> GeneratedAnswer: ...
```

`evidence` is the retrieved set **only**. A generator with any access to the whole corpus violates
FR-29. This is enforced by the signature, not by convention.

The generator may only emit markers for chunks present in `evidence` (ADR: [Architecture §7](04_SYSTEM_ARCHITECTURE.md#7-untrusted-content-and-prompt-injection) control 3).

---

## 9. Verification contract

### 9.1 `VerificationConfig`

```python
@dataclass(frozen=True)
class VerificationConfig:
    similarity_weight: float = 0.7      # Stage 2 formula
    overlap_weight: float = 0.3
    verified_threshold: float = 0.62    # calibrate in Phase 6
    review_threshold: float = 0.40      # calibrate in Phase 6
    check_numbers: bool = True
    check_contradiction: bool = True
    min_numeric_tokens: int = 2         # ignore "1", "2"
    rescale_cosine_to_unit_interval: bool = True
```

**Validation:** weights must sum to 1.0 (±1e-6), and `0 <= review_threshold < verified_threshold <= 1`.

### 9.2 `ClaimVerification`

```python
@dataclass(frozen=True)
class ClaimVerification:
    claim_id: str
    claim_text: str
    label: str                        # "Verified" | "Needs Review" | "Unsupported"
    support_score: float              # [0, 1] — the Stage 2 formula
    similarity: float                 # normalised component, [0, 1]
    overlap: float                    # token_overlap component, [0, 1]
    evidence: EvidenceChunk | None    # None when unresolved
    relevance_score: float | None     # that chunk's retrieval score — separate, labelled separately
    reason: str                       # reason code from §6.2
    explanation: str                  # user-facing, honest, includes what the label does NOT mean
```

**Invariants**

| # | Invariant |
|---|---|
| IV-1 | `0.0 <= support_score <= 1.0` |
| IV-2 | `support_score ≈ 0.7*similarity + 0.3*overlap` (exact to 1e-9) |
| IV-3 | `evidence is None` whenever `reason` is `unresolvable_reference` or `page_mismatch` |
| IV-4 | `label == "Verified"` requires a non-None `evidence` **and** `support_score >= verified_threshold` |
| IV-5 | `reason` is never empty |
| IV-6 | `explanation` never asserts proof, entailment, or truth |
| IV-7 | `relevance_score` is copied for display only and is never used in the support formula |

IV-7 is the second mechanical guard against score conflation. Combined with IR-5, the two scores
cannot be confused even by accident.

### 9.3 Verifier protocol

```python
class Verifier(Protocol):
    def verify(
        self,
        answer: GeneratedAnswer,
        retrieved: Sequence[RetrievalResult],
        config: VerificationConfig,
    ) -> tuple[ClaimVerification, ...]: ...
```

Pure function. No I/O, no network, no model. Same inputs ⇒ same outputs, always. This is what makes
the verifier's behaviour testable and the viva defensible.

---

## 10. Pipeline contract

### 10.1 `AnswerResponse`

The single object the UI renders. Nothing else.

```python
@dataclass(frozen=True)
class AnswerResponse:
    question: str
    answer: GeneratedAnswer
    retrieved: tuple[RetrievalResult, ...]
    verifications: tuple[ClaimVerification, ...]
    summary: VerificationSummary
    metrics: QueryMetrics
    warnings: tuple[str, ...] = ()
```

### 10.2 `VerificationSummary` and `QueryMetrics`

```python
@dataclass(frozen=True)
class VerificationSummary:
    verified: int
    needs_review: int
    unsupported: int
    uncited: int                       # claims with no marker
    unresolved_refs: int               # markers that did not resolve
    worst_support: float | None
    abstained: bool

    @property
    def headline(self) -> str:
        """Honest one-line summary. Must NOT be a single averaged score."""
```

`headline` is deliberately **not** an average. Averaging is how one bad claim hides behind three good
ones. It reports counts and the worst score.

```python
@dataclass(frozen=True)
class QueryMetrics:
    embed_ms: float
    retrieve_ms: float
    generate_ms: float
    verify_ms: float
    total_ms: float
    backend: str
    store: str
    generator: str
```

Timings exist for the Stage 3 metrics table. They are measured, never estimated, and never shown as
promises in the UI.

### 10.3 Public API

```python
class ResearchPipeline:
    def index(
        self,
        paths: Sequence[str | Path],
        config: PipelineConfig | None = None,
    ) -> IndexReport: ...

    def ask(
        self,
        question: str,
        top_k: int = 5,
        config: PipelineConfig | None = None,
    ) -> AnswerResponse: ...          # ← Phase 4

    def remove_document(self, source_id: str) -> bool: ...
    def reindex_document(self, path: str | Path) -> IndexReport: ...
    def index_stats(self) -> IndexStats: ...
```

**Phase 3 state.** Five of the six exist. `ask()` is absent because it returns an
`AnswerResponse`, whose `GeneratedAnswer` and `ClaimVerification` fields do not exist until Phase 4.

The retrieval it will call is implemented as `_retrieve(question, top_k)` — private on purpose.
`§10.3`'s rule "there is no other public entry point" is a structural guarantee that the UI cannot
bypass the orchestrator, and a second public retrieval method would weaken it. The blank-query
rejection (EC-05) and the empty-index guard (EC-21) are implemented and tested at that layer, so
`ask()` delegates rather than re-implements either.

Passing a second `config` to `index()` raises `ValueError`. A pipeline is configured once at
construction; letting it be reconfigured mid-session is how "which backend produced this vector?"
becomes unanswerable.

Rules the UI depends on:

- `index()` and `ask()` never raise for user-error conditions (bad file, blank question, empty index).
  They return a report/response carrying `failures` / `warnings` / `abstained`, so the UI can render
  the real reason. Genuine programmer errors still raise.
- `ask()` on an empty index returns an abstained response, not an exception.
- There is no other public entry point. The UI never touches `src` internals.

### 10.4 `PipelineConfig`

```python
@dataclass(frozen=True)
class PipelineConfig:
    chunk: ChunkConfig = ChunkConfig()
    top_k: int = 5
    embedding_backend: str = "tfidf"     # "tfidf" | "minilm"
    store: str = "memory"                # "memory" | "chroma"
    generator: str = "extractive"        # "extractive" | "flan-t5-small"   ← Phase 4
    persist_path: Path | None = None
    verification: VerificationConfig = VerificationConfig()                # ← Phase 4
    limits: ResourceLimits = ResourceLimits()
```

> **Current state (Phase 3):** `generator` and `verification` are **not yet implemented** and are
> absent from the code rather than stubbed. No code path can read a threshold that does not exist.
> They arrive in Phase 4 — decision D-16.

Validation now enforced in `__post_init__`: `top_k >= 1`; `embedding_backend` and `store` are known
values; and **`store == "chroma"` requires a `persist_path`**, since a Chroma store with nowhere to
persist is a configuration mistake that would otherwise surface as a runtime failure on first query.

```python
@dataclass(frozen=True)
class ResourceLimits:
    max_upload_mb: int = 50
    max_pages_per_document: int = 200
    total_page_warning: int = 1000       # "configurable target, not a guarantee"
```

`total_page_warning` is the only **soft** limit: exceeding it produces a warning naming the
operating target as a configuration value rather than a capacity guarantee, and indexing continues.
The first two refuse the file. `max_upload_bytes` is a derived property, so no caller can disagree
with `max_upload_mb` about how many bytes is too many.

---

## 11. Type map

```text
pdf_ingestion → DocumentPage, IngestFailure, reason codes
chunking      → EvidenceChunk, ChunkConfig
embeddings    → vectors (backend-specific), no project types
vector_store  → RetrievalResult, VectorStore protocol
generator     → GeneratedAnswer, Claim, CitationRef, AnswerGenerator protocol
verifier      → ClaimVerification, VerificationConfig, VerificationSummary, Verifier protocol
pipeline      → IndexReport, AnswerResponse, QueryMetrics, PipelineConfig, ResearchPipeline
app.py        → consumes only IndexReport, AnswerResponse, VerificationSummary
```

`src/models.py` holds every dataclass above. Protocols live beside their implementations. `app.py`
imports **only** from `pipeline` and the pure dataclasses — never from a leaf module, which enforces
FR-47 structurally.

---

## 12. Contract tests

These must exist and pass. They are the reason the contracts are trustworthy.

| # | Test | Guards |
|---|---|---|
| CT-01 | Same file + same config ⇒ identical `source_id` and `chunk_id` across two runs | IC-2, CT determinism |
| CT-02 | `chunk_id` contains no path separators, no absolute path | §4 |
| CT-03 | Page numbers are 1-based and contiguous | IP-1 |
| CT-04 | Every chunk's page number exists in its document | IC-2, IC-5 |
| CT-05 | No chunk spans two pages | IC-5 |
| CT-06 | `overlap_words == chunk_words` raises `ValueError` | FR-13 |
| CT-07 | `chunk_words <= 0` and `overlap_words < 0` raise `ValueError` | FR-13 |
| CT-08 | `RetrievalResult` has no `support_score` attribute | IR-5 |
| CT-09 | `ClaimVerification.support_score == 0.7*similarity + 0.3*overlap` | IV-2 |
| CT-10 | `support_score` always in `[0, 1]` across a fuzz set of inputs | IV-1 |
| CT-11 | `label == "Verified"` ⇒ `evidence is not None` and threshold met | IV-4 |
| CT-12 | Every `ClaimVerification` has a non-empty `reason` | IV-5 |
| CT-13 | No `explanation` contains a forbidden proof word (§9.2 IV-6 list) | IV-6 |
| CT-14 | `relevance_score` never appears in the support computation | IV-7 |
| CT-15 | `display_name` strips traversal, control chars, and truncates | SEC-01 |
| CT-16 | `headline` contains no single averaged percentage | §10.2 |
| CT-17 | Marker regex rejects `[S1 p5]` and `[S1, page 5]` | §8.3 |
| CT-18 | `ask("")` and `ask("   ")` raise `ValueError` | FR-23 |
| CT-19 | `PipelineConfig` weights not summing to 1.0 raise | §9.1 |
| CT-20 | `app.py` imports nothing from a leaf `src` module except dataclasses | FR-47 |