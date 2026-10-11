"""The single orchestration layer.

Every other module is a leaf: it does one job and knows nothing about the others. This one wires
them together, and it is the **only** place that does. The UI calls this module; it never
re-implements a retrieval or a scoring rule, which is requirement FR-47 enforced structurally
rather than by review.

Three behaviours here are contractual, not incidental:

* **User error is reported, not raised.** A bad file, an unreadable PDF or an over-limit upload
  produces an `IndexReport` carrying a real reason in `failures`, not an exception. The library
  panel can then show the user what actually happened instead of a stack trace -- and, more
  importantly, a partially-indexed collection never masquerades as a complete one.

* **A blank question is refused before any search happens.** Not after an empty result is
  explained away. EC-05 and FR-23 both require the refusal to come first, because the alternative
  is a retrieval that silently scores nothing and then reports "no evidence found".

* **`ask()` does not exist yet.** It arrives in Phase 4 with the generator and the verifier it
  needs. Exposing it now would mean inventing an answer type before anything can produce an
  answer. The retrieval it will call is `_retrieve`, and blank-query rejection is implemented and
  tested there, so `ask()` inherits it rather than re-implementing it.
"""

from __future__ import annotations

import re
import time
from collections.abc import Sequence
from pathlib import Path

from src.advisor import advise
from src.chunking import chunk_pages, light_stem
from src.embeddings import (
    EmbeddingBackend,
    EmbeddingBackendUnavailable,
    TfidfEmbeddingBackend,
    build_embedding_backend,
)
from src.generator import (
    AnswerGenerator,
    build_generator,
    insufficient_evidence_answer,
    api_key_is_configured,
)
from src.models import (
    USER_MESSAGES,
    AnswerResponse,
    ClaimVerification,
    CorrectionPlan,
    CoverageReport,
    DocumentPage,
    DocumentSummary,
    GeneratedAnswer,
    IndexReport,
    IndexStats,
    IngestFailure,
    PipelineConfig,
    QueryMetrics,
    Reason,
    RetrievalResult,
    VerificationConfig,
    VerificationSummary,
)
from src.pdf_ingestion import PDFIngestionError, load_document
from src.vector_store import VectorStore, build_vector_store
from src.verifier import Verifier, content_tokens

__all__ = [
    "ResearchPipeline",
    "PipelineConfig",
    "summarise",
    "query_coverage",
    "hosted_profile_available",
]


def hosted_profile_available() -> bool:
    """True when the hosted generator could actually run here.

    Re-exported from `pipeline` rather than imported by the UI from `generator`, because FR-47
    makes the pipeline the only module the view layer is allowed to reach. The UI needs to know
    whether to *offer* the hosted profile, and this is the supported way to ask.

    Offering a profile that would silently degrade would be worse than not offering it, so this
    returns False rather than optimistically True when the key is merely present but the model
    list could not be fetched.
    """
    return api_key_is_configured()


# Question scaffolding: the verbs, quantifiers and generic nouns that appear in *how a question is
# phrased* rather than *what it is about*. They carry no topical signal, so counting them as content
# terms dilutes the very ratio the gate depends on.
#
# Measured with the committed synthetic fixture, floor 0.50: on 10 answerable-paraphrase
# questions, stemming both sides plus dropping these terms moved the answered-rate from 4/10 to
# 8/10, and all 6 out-of-topic questions stayed refused. The words are deliberately few and
# generic; anything document-specific belongs in the document, not here, because a term removed
# from the denominator is a term that can never contribute evidence for an answer.
#
# The two remaining refusals are honest limits, not tuning failures: one asks about a synonym the
# document does not use (`tuned` where the document says `calibrated`), and one sits exactly on the
# 0.50 boundary. Raising the floor would trade a measured 0.000 false-abstention rate for them.
_QUESTION_SCAFFOLDING: frozenset[str] = frozenset(
    """
    much many more most less least often always never ever still already
    happen happens happened occur occurs occurred appear appears appeared
    pass passes passed between among during through over under above below
    list listed lists show shows shown give gives given make makes made
    use uses used using take takes took get gets got need needs needed
    kind sort type way ways thing things
    """.split()
)

# Alphanumeric runs, matching the tokenisation `content_tokens` already applies to the question.
# Both sides of the comparison must be split the same way or stems would not line up.
_COVERAGE_WORD = re.compile(r"[a-z0-9]+")


def query_coverage(
    question: str,
    retrieved: Sequence[RetrievalResult],
    scope: str = "retrieved",
) -> CoverageReport:
    """Which of the question's content words the retrieved passages actually contain.

    **This replaced a threshold on `relevance_score`, and that is the finding, not a
    preference.** On the 48 labelled cases in
    [tests/data/abstention_cases.jsonl](../tests/data/abstention_cases.jsonl) the two
    classes overlap on cosine: answerable top-1 scores run 0.14-0.26 and unanswerable
    ones 0.07-0.19. A floor at 0.18 catches 8 of 10 unanswerable questions and
    simultaneously kills 5 of 8 answerable ones. There is no clean cut, because TF-IDF
    cosine over shared academic prose is dominated by vocabulary both classes have, so it
    measures *register* more than *relevance*.

    Coverage asks the question the gate actually needs answered: are the distinctive
    words of this question present in what we retrieved.

    **Both sides of the comparison are stemmed, and that is what makes the measure
    morphological rather than literal.** The original implementation compared raw content
    tokens to the raw passage text with substring containment, so `readings` did not match
    `reading` and `figures` did not match `figure`. Measured against the committed
    synthetic fixture at the 0.50 floor, that refused 6 of 10 *answerable* paraphrase
    questions -- a real cost, not a rounding error.

    Stemming the question terms and the passage tokens through the same `light_stem`
    fixes the morphology. It is not monotonic in the coverage ratio, though, and the
    reason is worth recording: substring matching was what the old code used, and once
    `lights` reduces to `light`, that stem matched "lightweight" and answered "What causes
    the northern lights?" from a document about neither. So the match is now **token
    equality over stems**. Nothing is lost by it -- stemming already makes `chunk` agree
    with `chunking` on its own -- and the spurious prefix matches go away.

    **Two independent reductions, one signal.** Besides stemming, question scaffolding
    (`much`, `happens`, `listed`, ...) is removed before the ratio is taken, because those
    words describe the phrasing of a question rather than its subject. See
    `_QUESTION_SCAFFOLDING`.

    What this deliberately does **not** do is handle synonymy: a passage saying `calibrated`
    does not match a question saying `tuned`, and coverage scores that zero. Two of the ten
    probe questions stay refused after this change, one for that reason and one on the 0.50
    boundary. Closing the first needs entailment, not a longer normalisation table, and it is
    recorded as a limit rather than papered over.

    Returns `covered` and `missing` so the refusal can name them. A gate that reports only
    a score asks the user to trust a number they cannot inspect.
    """
    if scope == "top":
        pool = retrieved[:1]
    elif scope == "retrieved":
        pool = retrieved
    else:
        raise ValueError(f"unknown coverage scope: {scope!r}; expected 'retrieved' or 'top'")

    # Terms are reduced to stems for matching, but the report carries the **words the user
    # actually typed**. Showing a stem would put `boil` in the refusal message for a user who
    # asked about "boiling", which is both unhelpful and simply untrue -- the report is quoted
    # back to them in `insufficient_evidence_answer` and is meant to be checkable against their
    # own question. A test asserts the verbatim term survives to the UI.
    surface_terms = {
        term for term in content_tokens(question) if term not in _QUESTION_SCAFFOLDING
    }
    terms = {light_stem(term) for term in surface_terms}
    if not terms:
        return CoverageReport(covered=(), missing=())

    # Token equality over stems, not substring containment. Substring matching was the previous
    # behaviour and it had to go: with stemming in front of it, `lights` reduces to `light`, which
    # then matched "lightweight" anywhere in the corpus and answered "What causes the northern
    # lights?" from a document about neither. Stemming already makes `chunk` and `chunking` agree
    # on their own, so the prefix overlap that substring matching was there to provide is no longer
    # needed, and its false positives are the only thing it still contributes.
    pool_stems = {
        light_stem(token)
        for result in pool
        for token in _COVERAGE_WORD.findall(result.chunk.text.lower())
    }
    covered_stems = terms & pool_stems
    covered = tuple(sorted(term for term in surface_terms if light_stem(term) in covered_stems))
    missing = tuple(
        sorted(term for term in surface_terms if light_stem(term) not in covered_stems)
    )
    return CoverageReport(covered=covered, missing=missing)


def summarise(
    answer: GeneratedAnswer,
    verifications: Sequence[ClaimVerification],
) -> VerificationSummary:
    """Build the counts the UI shows. Counts and a worst case -- never a mean.

    A single averaged percentage would let one unsupported claim hide behind four verified ones, and
    would read as a confidence score the system has no way to justify. CT-16 asserts that no average
    appears in ``headline``.
    """
    verified = sum(1 for v in verifications if v.label == "Verified")
    needs_review = sum(1 for v in verifications if v.label == "Needs Review")
    unsupported = sum(1 for v in verifications if v.label == "Unsupported")
    uncited = sum(1 for v in verifications if v.reason == Reason.NO_MARKER)
    unresolved = sum(1 for v in verifications if v.reason == Reason.UNRESOLVABLE_REFERENCE)
    scores = [v.support_score for v in verifications]
    return VerificationSummary(
        verified=verified,
        needs_review=needs_review,
        unsupported=unsupported,
        uncited=uncited,
        unresolved_refs=unresolved,
        worst_support=min(scores) if scores else None,
        abstained=answer.abstained,
    )


class ResearchPipeline:
    """Index documents and retrieve evidence from them.

    Construction is cheap and side-effect free: no model is loaded, no directory is created, no
    network call is made. Everything expensive happens on `index()`, which is what lets the Streamlit
    app start in under the NFR-06 budget on a machine with no model weights at all.
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self._config = config or PipelineConfig()
        self._backend: EmbeddingBackend = build_embedding_backend(self._config.embedding_backend)
        self._store: VectorStore = build_vector_store(
            self._config.store, persist_path=self._config.persist_path
        )
        self._store.set_similarity(self._backend.similarity, self._backend.name)
        self._generator: AnswerGenerator = build_generator(self._config.generator)
        self._verifier = Verifier(similarity_fn=self._claim_similarity)

        self._summaries: dict[str, DocumentSummary] = {}
        self._page_counts: dict[str, int] = {}
        self._chunk_counts: dict[str, int] = {}
        self._total_pages = 0
        self._warnings: list[str] = []
        self._degraded_reason: str | None = None
        self._stale_chunks = 0
        self._restored_chunks = 0
        self._last_report: IndexReport | None = None

        self._refit_lexical_backend()

    # -- introspection --------------------------------------------------------

    @property
    def config(self) -> PipelineConfig:
        return self._config

    @property
    def backend_name(self) -> str:
        return self._backend.name

    @property
    def store_name(self) -> str:
        return self._store.name

    @property
    def degraded_reason(self) -> str | None:
        """Why the configured profile is not the one running, or ``None``.

        Surfaced in the UI without exception. A degraded run that looks identical to a full run is
        dishonest, and this is the value that makes the difference visible.
        """
        return self._degraded_reason

    @property
    def restored_chunks(self) -> int:
        """Chunks recovered from a persisted index at startup, or 0 for a fresh index.

        Non-zero means this process reused an existing index instead of re-reading the PDFs,
        which is the observable behind EC-15. Measured, never assumed.
        """
        return self._restored_chunks

    @property
    def stale_chunks(self) -> int:
        """Chunks embedded by a *previous* backend, so the current one cannot score them.

        Zero in every normal run. Non-zero only after a mid-session degradation, and the UI must
        say so rather than presenting those documents as searchable.
        """
        return self._stale_chunks

    @property
    def last_report(self) -> IndexReport | None:
        """The most recent ``index()`` report, including its failures, or ``None``.

        The UI reads this to show why a file did not index. Re-running ``index([])`` to discover that
        would be absurd; keeping the last report is the whole reason the property exists.
        """
        return self._last_report

    @property
    def warnings(self) -> tuple[str, ...]:
        """Warnings from the most recent indexing run."""
        return self._last_report.warnings if self._last_report else ()

    @property
    def failures(self) -> tuple[IngestFailure, ...]:
        """Files from the most recent run that did not index, with their real reasons."""
        return self._last_report.failures if self._last_report else ()

    def index_stats(self) -> IndexStats:
        return IndexStats(
            document_count=len(self._summaries),
            total_pages=self._total_pages,
            total_chunks=self._store.count(),
            backend=self._backend.name,
            store=self._store.name,
            persist_path=(
                str(self._config.persist_path) if self._config.persist_path else None
            ),
            documents=tuple(self._summaries.values()),
        )

    def reconfigure(self, config: PipelineConfig) -> None:
        """Adopt a new configuration, discarding the index if the embedding backend changed.

        The UI exposes settings, so this exists. Two rules make it safe:

        * **The index is dropped when the backend changes.** Vectors from TF-IDF and from MiniLM
          live in different spaces; comparing a query against the wrong one is meaningless, and
          silently keeping them would be worse than making the user re-index.
        * **A pipeline keeps one store for its lifetime.** Swapping `memory` for `chroma` mid-session
          would need a migration nobody asked for, so it is refused with a message saying to restart.
        """
        if config.embedding_backend != self._config.embedding_backend and self._store.count() > 0:
            self._reset_index()
            self._stale_chunks = 0
        if config.store != self._config.store:
            raise ValueError(
                "the vector store cannot be changed on a live pipeline; restart the app to switch "
                f"between {self._config.store!r} and {config.store!r}"
            )
        self._config = config
        # Only rebuild the backend when the profile genuinely changed. Rebuilding it unconditionally
        # threw away the fitted TF-IDF vocabulary while the store kept its chunks, so the UI passed
        # its "is the index empty?" check and the next query died with `has not been fitted`. Two
        # pieces of state that must agree were being told different stories.
        if config.embedding_backend != self._backend.name:
            self._backend = build_embedding_backend(config.embedding_backend)
            self._store.set_similarity(self._backend.similarity, self._backend.name)
        self._generator = build_generator(config.generator)
        self._verifier = Verifier(similarity_fn=self._claim_similarity)
        self._degraded_reason = None

    def _reset_index(self) -> None:
        self._summaries.clear()
        self._page_counts.clear()
        self._chunk_counts.clear()
        self._total_pages = 0
        self._restored_chunks = 0
        self._store = build_vector_store(
            self._config.store, persist_path=self._config.persist_path
        )
        self._store.set_similarity(self._backend.similarity, self._backend.name)

    # -- indexing -------------------------------------------------------------

    def index(
        self,
        paths: Sequence[str | Path],
        config: PipelineConfig | None = None,
    ) -> IndexReport:
        """Ingest every path given and return what actually made it into the index.

        One bad file fails that file, not the batch, and the batch report says so. Refusing the
        whole upload because one file was a `.txt` would be technically safe and practically
        useless.
        """
        started = time.perf_counter()
        if config is not None and config is not self._config:
            raise ValueError(
                "a pipeline is configured at construction; build a new one to change its profile"
            )

        summaries: list[DocumentSummary] = []
        failures: list[IngestFailure] = []
        warnings: list[str] = []

        for path in paths:
            try:
                pages = load_document(path, self._config.limits)
            except PDFIngestionError as exc:
                failures.append(
                    IngestFailure(
                        filename=Path(path).name, reason=exc.reason, message=exc.message
                    )
                )
                continue
            except OSError as exc:
                failures.append(
                    IngestFailure(
                        filename=Path(path).name,
                        reason=Reason.CORRUPT_PDF,
                        message=f"That file could not be read: {exc.strerror or exc}.",
                    )
                )
                continue

            chunks = chunk_pages(pages, self._config.chunk)
            if not chunks:
                failures.append(
                    IngestFailure(
                        filename=Path(path).name,
                        reason=Reason.ZERO_CHUNKS,
                        message=USER_MESSAGES[Reason.ZERO_CHUNKS],
                    )
                )
                continue

            source_id = pages[0].source_id
            try:
                vectors = self._backend.embed_documents([chunk.text for chunk in chunks])
            except EmbeddingBackendUnavailable as exc:
                # Degrade rather than index blind. An index whose vectors do not exist is an index
                # that will answer every question wrongly and look confident.
                self._degraded_reason = str(exc)
                self._swap_to_tfidf()
                try:
                    vectors = self._backend.embed_documents([chunk.text for chunk in chunks])
                except EmbeddingBackendUnavailable as retry_exc:  # pragma: no cover
                    failures.append(
                        IngestFailure(
                            filename=Path(path).name,
                            reason=Reason.EMPTY_INDEX,
                            message=f"No embedding backend is available: {retry_exc}",
                        )
                    )
                    continue
                warnings.append(f"semantic backend unavailable, using {self._backend.name}")

            self._store.add(list(chunks), vectors)

            summary = DocumentSummary(
                source_id=source_id,
                display_name=pages[0].display_name,
                page_count=len(pages),
                chunk_count=len(chunks),
                status="indexed",
                engine=self._backend.name,
            )
            self._summaries[source_id] = summary
            self._page_counts[source_id] = len(pages)
            self._chunk_counts[source_id] = len(chunks)
            self._total_pages += len(pages)
            summaries.append(summary)
            warnings.extend(_page_warnings(pages))

        self._warnings = warnings
        self._store.persist()
        if self._total_pages > self._config.limits.total_page_warning:
            warnings.append(
                f"This collection holds {self._total_pages} pages, above the operating target of "
                f"{self._config.limits.total_page_warning}. That target is a configuration value, "
                "not a capacity guarantee."
            )
        self._last_report = IndexReport(
            documents=tuple(summaries),
            total_pages=self._total_pages,
            total_chunks=self._store.count(),
            backend=self._backend.name,
            store=self._store.name,
            persist_path=(str(self._config.persist_path) if self._config.persist_path else None),
            elapsed_seconds=time.perf_counter() - started,
            warnings=tuple(dict.fromkeys(warnings)),
            failures=tuple(failures),
        )
        return self._last_report

    def remove_document(self, source_id: str) -> bool:
        """Remove one document from the index. ``False`` if it was not there."""
        removed = self._store.delete_document(source_id)
        if not removed:
            return False
        self._summaries.pop(source_id, None)
        self._total_pages -= self._page_counts.pop(source_id, 0)
        self._chunk_counts.pop(source_id, None)
        self._store.persist()
        return True

    def reindex_document(self, path: str | Path) -> IndexReport:
        """Re-read one document, replacing its old chunks rather than adding to them.

        The content-derived IDs make this safe: the replacement chunks carry the same ``chunk_id``s,
        so nothing is duplicated and no reference left dangling by the old index points at a
        different passage. The file is read twice -- once to learn which ``source_id`` it owns, once
        to build fresh chunks -- because ``source_id`` depends on the page count and there is no
        cheaper honest way to get it.
        """
        try:
            pages = load_document(path, self._config.limits)
        except PDFIngestionError as exc:
            return self._failed_report(
                (IngestFailure(filename=Path(path).name, reason=exc.reason, message=exc.message),)
            )
        except OSError as exc:
            return self._failed_report(
                (
                    IngestFailure(
                        filename=Path(path).name,
                        reason=Reason.CORRUPT_PDF,
                        message=f"That file could not be read: {exc.strerror or exc}.",
                    ),
                )
            )

        self.remove_document(pages[0].source_id)
        return self.index([path])

    def _failed_report(self, failures: tuple[IngestFailure, ...]) -> IndexReport:
        """A report describing a run that indexed nothing.

        Shape-identical to a successful report so the UI has one code path. The distinction the
        user sees is `is_empty()` and the populated `failures`, not a different object type.
        """
        return IndexReport(
            documents=(),
            total_pages=self._total_pages,
            total_chunks=self._store.count(),
            backend=self._backend.name,
            store=self._store.name,
            persist_path=(str(self._config.persist_path) if self._config.persist_path else None),
            elapsed_seconds=0.0,
            failures=failures,
        )

    # -- query ----------------------------------------------------------------

    def ask(self, question: str, top_k: int | None = None) -> AnswerResponse:
        """Answer a question from the index, then verify every claim against its citation.

        The order of operations *is* the design:

        1. **Refuse a blank question before anything else** (EC-05), rather than explaining away an
           empty result afterwards.
        2. **Retrieve.** An empty index abstains here instead of producing a confident-looking answer.
        3. **Refuse weakly-matched evidence before generating** (FR-33, R-24). A non-empty index
           returning five unrelated passages is not an answer, and building one only to label it
           `Unsupported` afterwards is the failure this step removes.
        4. **Generate from the retrieved set only.** The generator's signature gives it no access to
           the corpus, so it cannot quote something that was not retrieved.
        5. **Verify.** Every claim gets a label, a reason code and an explanation.

        Returns an `AnswerResponse` for every user-facing case including abstention, so the UI has one
        code path. Genuine programmer errors -- a blank question, a non-positive `top_k` -- still
        raise, because a silent response would hide a bug in the caller.
        """
        started = time.perf_counter()
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        effective_top_k = self._config.top_k if top_k is None else top_k
        if effective_top_k < 1:
            raise ValueError("top_k must be at least 1")

        warnings: list[str] = []
        if self._stale_chunks:
            warnings.append(
                f"{self._stale_chunks} indexed chunk(s) were embedded by a different backend and "
                "cannot be scored by the current one. Re-index to include them."
            )
        if self._degraded_reason:
            warnings.append(f"Running in degraded mode: {self._degraded_reason}")

        # An empty index is a state to render, not an exception to catch: abstain, with the same
        # response shape as a successful query.
        if self._store.count() == 0:
            answer = self._generator.generate(question, (), effective_top_k)
            return self._response(
                question,
                answer,
                (),
                (),
                started,
                embed_ms=0.0,
                retrieve_ms=0.0,
                generate_ms=0.0,
                verify_ms=0.0,
                warnings=warnings,
            )

        clock = time.perf_counter()
        query_vector = self._backend.embed_query(question.strip())
        embed_ms = (time.perf_counter() - clock) * 1000

        clock = time.perf_counter()
        retrieved = tuple(self._store.query(query_vector, effective_top_k))
        retrieve_ms = (time.perf_counter() - clock) * 1000

        # 3. **Refuse weak evidence before generating, not after.** The empty-index case
        #    above is a count gate. This is the quality gate, and it exists because
        #    measurement showed the count gate was the only one: with a non-empty index
        #    the extractive generator was quoting the least-irrelevant sentence it could
        #    find for questions about photosynthesis and the northern lights, and the
        #    verifier was then honestly labelling those claims. Checking here means a claim
        #    is never manufactured only to be labelled afterwards (R-24, FR-33).
        abstention = self._config.abstention
        if abstention.enabled:
            coverage = query_coverage(question, retrieved, abstention.coverage_scope)
            # A question with no content terms left after stopword removal carries no
            # signal either way, and `coverage.value` is 1.0 for it. Abstaining there
            # would be a guess dressed as a measurement, so the gate stays shut.
            if coverage.terms and coverage.value < abstention.min_query_coverage:
                clock = time.perf_counter()
                answer = insufficient_evidence_answer(coverage, abstention.min_query_coverage)
                return self._response(
                    question,
                    answer,
                    retrieved,
                    (),
                    started,
                    embed_ms=embed_ms,
                    retrieve_ms=retrieve_ms,
                    generate_ms=(time.perf_counter() - clock) * 1000,
                    verify_ms=0.0,
                    warnings=warnings,
                )

        clock = time.perf_counter()
        evidence = [result.chunk for result in retrieved]
        answer = self._generator.generate(question, evidence, effective_top_k)
        generate_ms = (time.perf_counter() - clock) * 1000

        clock = time.perf_counter()
        verifications = self._verifier.verify(answer, retrieved, self._verification_config())
        verify_ms = (time.perf_counter() - clock) * 1000

        degraded = getattr(self._generator, "degraded_reason", None)
        if degraded:
            warnings.append(f"Generator degraded: {degraded}")

        return self._response(
            question,
            answer,
            retrieved,
            verifications,
            started,
            embed_ms=embed_ms,
            retrieve_ms=retrieve_ms,
            generate_ms=generate_ms,
            verify_ms=verify_ms,
            warnings=warnings,
        )

    def _claim_similarity(self, claim: str, chunk_text: str) -> float:
        """Semantic similarity for one claim against one passage, using the active backend.

        TF-IDF was fitted on the corpus, so a claim scored against a passage uses the *same*
        vocabulary the retrieval used -- the two numbers are comparable in origin even though they
        answer different questions.

        Cosine over non-negative TF-IDF weights is already `[0, 1]`, so the verifier's
        ``rescale_cosine_to_unit_interval`` must stay off for this backend. Turning it on would map an
        unrelated claim from 0.0 to 0.5 and inflate every support score; the asymmetry between the two
        profiles is real, documented in Architecture section 5.2, and handled here rather than hidden.
        """
        if self._stale_chunks:
            # Those chunks were embedded by a different backend, so any score here would
            # be arithmetic on incomparable vectors. Return 0 and let the label reflect
            # it rather than inventing a number.
            return 0.0
        return float(
            self._backend.similarity(
                self._backend.embed_query(claim),
                self._backend.embed_documents([chunk_text]),
            )[0]
        )

    def _verification_config(self) -> VerificationConfig:
        """The verifier's config, with the rescale flag set by what the backend actually returns.

        `rescale_cosine_to_unit_interval` defaults to `True` because raw cosine on MiniLM embeddings
        can be negative. TF-IDF cosine over non-negative weights is *already* in `[0, 1]`, so
        rescaling it would map an unrelated claim from 0.0 to 0.5 and inflate every support score --
        the system would look more confident the less the evidence supported it.

        Deciding this from the backend rather than from the config file is deliberate: the flag
        describes a property of the similarity function, and only the backend knows it.
        """
        from dataclasses import replace

        base = self._config.verification
        needs_rescale = base.rescale_cosine_to_unit_interval and self._backend.name == "minilm"
        if needs_rescale == base.rescale_cosine_to_unit_interval:
            return base
        return replace(base, rescale_cosine_to_unit_interval=needs_rescale)

    def _response(
        self,
        question: str,
        answer: GeneratedAnswer,
        retrieved: tuple[RetrievalResult, ...],
        verifications: tuple[ClaimVerification, ...],
        started: float,
        *,
        embed_ms: float,
        retrieve_ms: float,
        generate_ms: float,
        verify_ms: float,
        warnings: Sequence[str],
    ) -> AnswerResponse:
        summary = summarise(answer, verifications)
        return AnswerResponse(
            question=question,
            answer=answer,
            retrieved=retrieved,
            verifications=verifications,
            summary=summary,
            # Corrections are derived here, from the verifications just computed, so the advice and
            # the labels cannot disagree. An abstained answer produces no verifications and
            # therefore no corrections, which is correct: nothing was checked, so there is nothing
            # to advise about. `advise` is pure, so this costs no I/O and is safe on the hot path.
            corrections=advise(verifications, headline=summary.headline),
            metrics=QueryMetrics(
                embed_ms=embed_ms,
                retrieve_ms=retrieve_ms,
                generate_ms=generate_ms,
                verify_ms=verify_ms,
                total_ms=(time.perf_counter() - started) * 1000,
                backend=self._backend.name,
                store=self._store.name,
                generator=answer.generator,
            ),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    # -- citation audit -------------------------------------------------------

    def review(self, answer: AnswerResponse) -> CorrectionPlan:
        """Re-derive the correction plan for a response already in hand.

        Exists so the UI can offer "check this answer again" without re-running the query, and so a
        caller holding a response from elsewhere can obtain the same advice the pipeline produced.
        It reads `answer.verifications` and nothing else -- in particular it does not re-verify,
        because a second verification pass over the same data would produce the same labels and
        calling it "re-checking" would misrepresent what happened.
        """
        return advise(answer.verifications, headline=answer.summary.headline)

    # -- retrieval ------------------------------------------------------------

    def _refit_lexical_backend(self) -> None:
        """Rebuild a persisted TF-IDF vocabulary on startup.

        A TF-IDF vector is only comparable to another vector built from the same vocabulary, and
        that vocabulary lives in memory. A restarted process has persisted *vectors* in Chroma but
        not the mapping that produced them, so without this step a second run could not query the
        index at all (EC-15).

        This is a lexical refit from the stored chunk texts, not re-embedding: no model is involved
        and the result is deterministic. The semantic backend does not need it -- its weights are
        on disk and its vectors are not vocabulary-dependent.
        """
        if not isinstance(self._backend, TfidfEmbeddingBackend):
            return
        restore = getattr(self._store, "stored_texts", None)
        if restore is None:
            return
        texts = [text for text in restore() if text]
        if texts:
            self._backend.fit(texts)
            self._restored_chunks = len(texts)

    def _swap_to_tfidf(self) -> None:
        """Fall back to the lexical backend, keeping whatever is already indexed.

        The store's vectors were produced by whichever backend was active, so swapping the backend
        does **not** make existing vectors comparable to new queries. Two consequences, both
        deliberate:

        * Already-indexed chunks keep their old vectors and become unreachable by the new backend.
          They are reported as `stale_chunks` rather than silently returned as if they had been
          scored by the profile now in use.
        * The reason is recorded in `degraded_reason` so the UI can say why.

        The alternative -- rebuilding the whole index mid-upload -- would be correct and would
        surprise the user by taking far longer than they asked for.
        """
        if self._backend.name == "tfidf":
            return
        self._backend = build_embedding_backend("tfidf")
        self._store.set_similarity(self._backend.similarity, self._backend.name)
        self._stale_chunks = self._store.count()

    def _retrieve(self, question: str, top_k: int | None = None) -> list[RetrievalResult]:
        """Return the top-k most relevant chunks, or nothing.

        Rejects a blank question *before* touching the store. An empty collection is also refused
        here rather than turned into an empty result, so that "you asked nothing" and "you have no
        documents" can never be confused for "there is no relevant evidence".
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        if top_k is None:
            top_k = self._config.top_k
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if self._store.count() == 0:
            raise ValueError(
                "the index is empty; index at least one document before asking a question"
            )

        query_vector = self._backend.embed_query(question.strip())
        return self._store.query(query_vector, top_k)


def _page_warnings(pages: Sequence[DocumentPage]) -> list[str]:
    """Surface per-page oddities once, not once per page.

    Injection-shaped text is the important one: the user needs to know a document is trying to
    issue instructions, and they need to hear it once.
    """
    notes: list[str] = []
    low_text = sum(1 for page in pages if "low_text_page" in page.warnings)
    if low_text:
        notes.append(f"{low_text} of {len(pages)} pages yielded very little text.")
    reference_pages = [page for page in pages if "reference_page_detected" in page.warnings]
    if reference_pages:
        # Said once, because the user's response is to know it is handled -- not to be told per page.
        notes.append(
            f"{len(reference_pages)} of {len(pages)} pages look like a reference list and are "
            "ranked below prose, so a citation is not quoted as if it were a finding. They stay "
            "searchable if the question is about the references themselves."
        )
    for page in pages:
        for warning in page.warnings:
            if warning.startswith("injection_pattern_detected:"):
                notes.append(
                    f"{page.display_name} page {page.page_number} contains instruction-like text "
                    f"({warning.split(':', 1)[1]}). It is treated as evidence, never as an instruction."
                )
    return notes