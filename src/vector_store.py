"""Vector stores: an in-memory implementation for tests, a Chroma adapter for real use.

Both stores answer the same question -- *given a query vector, which stored chunks are most
relevant?* -- and both produce the **same shape of answer**: `RetrievalResult` objects, ranked from
1, with `relevance_score` normalised to `[0, 1]` by the embedding backend that produced the
vectors.

Three decisions worth stating, because each one exists to stop a specific quiet failure:

1. **`top_k` is clamped inside `query`, not by the caller.** IR-4 says the result count is
   `min(top_k, collection_size)`. Clamping in one place means no caller can forget it, and a UI
   that asks for 10 chunks from a 3-chunk library gets 3 rows instead of an exception.

2. **Ties break on `chunk_id`, never on insertion order.** `(-relevance_score, chunk_id)` makes the
   ranking a pure function of the data. Without it, two runs over the same corpus can return the
   same chunks in a different order, and "deterministic" becomes a claim rather than a property.

3. **Chroma's ranking is re-scored by our own similarity function.** Chroma's HNSW index is
   approximate and its distance metric is whatever `hnsw:space` says. Rather than trust it, the
   adapter asks Chroma for candidates and then recomputes relevance with the same backend function
   the in-memory store uses, so the two stores cannot drift apart in what a score means. The cost
   is that Chroma's candidate recall is still approximate -- recorded honestly in
   [Architecture 8](../../docs/04_SYSTEM_ARCHITECTURE.md#8-determinism), not hidden here.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np
from scipy import sparse

from src.embeddings import row_count
from src.models import EvidenceChunk, RetrievalResult

__all__ = [
    "VectorStore",
    "InMemoryVectorStore",
    "ChromaVectorStore",
    "ChromaUnavailable",
    "build_vector_store",
]

# Chroma candidate-list depth for HNSW search. Generous enough to make search exhaustive
# at this project's corpus sizes. Named so the trade-off is visible in the code and
# reported rather than buried in a config file.
SEARCH_EF = 256

# How many times top_k to ask Chroma for before ranking the candidates ourselves.
# Every extra candidate costs one embedding comparison; the point is to give the
# deterministic tie-break a wide enough pool that it can actually apply.
CANDIDATE_OVERSAMPLE = 4

# Multiplier applied to a bibliography page's retrieval score. Low enough that prose addressing the
# question wins, high enough that a question *about* the references still reaches them. Not zero:
# see `_sorted_results`.
REFERENCE_PAGE_DEMOTION = 0.35


class VectorStoreError(RuntimeError):
    """The store cannot serve a query."""


class ChromaUnavailable(VectorStoreError):
    """`chromadb` is not installed, or its persistent directory cannot be opened."""


@runtime_checkable
class VectorStore(Protocol):
    """What the pipeline requires of a store."""

    name: str

    def add(self, chunks: list[EvidenceChunk], vectors: Any) -> None: ...

    def query(self, query_vector: Any, top_k: int) -> list[RetrievalResult]: ...

    def count(self) -> int: ...

    def delete_document(self, source_id: str) -> int: ...

    def persist(self) -> None: ...


def _sorted_results(
    scored: list[tuple[float, EvidenceChunk]], backend: str, limit: int
) -> list[RetrievalResult]:
    """Rank by score then by ``chunk_id``, and hand back 1-based contiguous ranks.

    Shared by both stores on purpose: if each implemented its own sort, "the same query returns
    the same order" would be two separate promises instead of one.

    A bibliography page is demoted rather than dropped. Ranking it on equal terms lets a question
    about, say, the proposed topology return the "References" page and cite a citation as though
    it were a finding. Dropping it would be worse -- an unresolvable citation -- so the chunk stays
    retrievable and merely yields to prose that actually addresses the question.
    """
    adjusted = [
        (score * (REFERENCE_PAGE_DEMOTION if chunk.is_reference_page else 1.0), chunk)
        for score, chunk in scored
    ]
    ordered = sorted(adjusted, key=lambda pair: (-pair[0], pair[1].chunk_id))
    return [
        RetrievalResult(rank=index, chunk=chunk, relevance_score=float(score), backend=backend)
        for index, (score, chunk) in enumerate(ordered[:limit], start=1)
    ]


def _dense_rows(vectors: Any) -> np.ndarray:
    """Materialise a vector batch as a dense float array.

    Chroma stores dense embeddings on disk, so a sparse TF-IDF matrix has to become dense to be
    handed over. That is the cost of choosing Chroma with a sparse backend, and it is a real one:
    the same corpus costs `chunks x vocabulary` floats instead of a few non-zeros per chunk. The
    in-memory store never does this, which is why it remains the memory-safe default.
    """
    if sparse.issparse(vectors):
        return np.asarray(vectors.todense(), dtype=np.float32)
    return np.asarray(vectors, dtype=np.float32)


def _as_row(vector: Any) -> Any:
    """Coerce one stored vector to a 1-row matrix, keeping its kind.

    A sparse row stays a sparse row; a dense vector stays a 1-D array. Mixing them would force
    ``_rows`` to densify, which is the memory blow-up this module exists to avoid.
    """
    if sparse.issparse(vector):
        return sparse.csr_matrix(vector)
    return np.asarray(vector).ravel()


def _rows(rows: list[Any]) -> Any:
    """Stack stored rows into one matrix, keeping sparse sparse.

    Densifying a TF-IDF matrix would cost ``chunks x vocabulary`` floats; at the project's
    operating target that is gigabytes. Callers pass the full ordered row list, which is what
    makes a deletion impossible to get subtly wrong.
    """
    usable = [row for row in rows if row is not None and np.size(row) > 0]
    if not usable:
        return None
    if sparse.issparse(usable[0]):
        return sparse.vstack(usable, format="csr")
    return np.vstack([np.atleast_2d(row) for row in usable])


class InMemoryVectorStore:
    """Deterministic, in-process, no persistence. The test profile and the default.

    Holds the chunks themselves, because a citation needs the filename and page and there is no
    index to read them back from. Holding them also means the store can be introspected in a test
    without reaching into private state elsewhere.
    """

    name = "memory"

    def __init__(self) -> None:
        self._chunks: dict[str, EvidenceChunk] = {}
        self._order: list[str] = []
        self._rows: dict[str, Any] = {}
        self._matrix_cache: Any = None
        self._score_fn: Any = None
        self._scorer_name = "unset"
        self._lock = threading.Lock()

    # -- wiring ---------------------------------------------------------------

    def set_similarity(self, score_fn: Any, scorer_name: str) -> None:
        """Install the embedding backend's similarity function and its name.

        The store has no opinion about cosine, TF-IDF or rescaling. Handing it the backend's own
        function is what keeps a store from inventing a second, subtly different scoring rule.

        ``scorer_name`` is recorded on every result because `RetrievalResult.backend` means *which
        similarity produced this score* -- which is the embedding backend, not the store. A result
        labelled `memory` would say nothing about how 0.72 was arrived at.
        """
        self._score_fn = score_fn
        self._scorer_name = scorer_name

    # -- VectorStore ----------------------------------------------------------

    def add(self, chunks: list[EvidenceChunk], vectors: Any) -> None:
        """Add or replace chunks, keyed by ``chunk_id``.

        Replace rather than append so that re-indexing the same file is idempotent (EC-15): the
        IDs are content-derived, so a second pass produces the same IDs and must not duplicate.
        """
        if len(chunks) != row_count(vectors):
            raise VectorStoreError(
                f"chunk/vector length mismatch: {len(chunks)} chunks, {row_count(vectors)} vectors"
            )
        with self._lock:
            for position, chunk in enumerate(chunks):
                if chunk.chunk_id not in self._chunks:
                    self._order.append(chunk.chunk_id)
                self._chunks[chunk.chunk_id] = chunk
                self._rows[chunk.chunk_id] = _as_row(vectors[position])
            self._matrix_cache = None

    def query(self, query_vector: Any, top_k: int) -> list[RetrievalResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if self._score_fn is None:
            raise VectorStoreError("no similarity function installed")
        if not self._order:
            return []
        limit = min(top_k, len(self._order))

        ids = self._order
        matrix = self._matrix()
        scores = self._score_fn(query_vector, matrix)
        if len(scores) != len(ids):  # pragma: no cover - guarded by add()
            raise VectorStoreError("vector store is inconsistent; re-index the collection")
        scored = [(float(score), self._chunks[chunk_id]) for chunk_id, score in zip(ids, scores)]
        return _sorted_results(scored, self._scorer_name, limit)

    def count(self) -> int:
        return len(self._order)

    def delete_document(self, source_id: str) -> int:
        """Remove every chunk of one document. Returns how many were removed."""
        with self._lock:
            doomed = [cid for cid in self._order if self._chunks[cid].source_id == source_id]
            if not doomed:
                return 0
            for chunk_id in doomed:
                self._chunks.pop(chunk_id, None)
                self._rows.pop(chunk_id, None)
            self._order = [cid for cid in self._order if cid not in set(doomed)]
            self._matrix_cache = None
            return len(doomed)

    def persist(self) -> None:
        """No-op. This store is deliberately not persistent."""
        return None

    # -- internals ------------------------------------------------------------

    def _matrix(self) -> Any:
        """Assemble the query matrix, cached until the next mutation.

        Built from a per-chunk row dict rather than kept as one contiguous matrix, so a deletion
        never has to work out which rows shifted. Sparse stays sparse, dense stays dense.
        """
        if self._matrix_cache is None:
            self._matrix_cache = _rows([self._rows[cid] for cid in self._order])
        return self._matrix_cache


class ChromaVectorStore:
    """Persistent adapter over `chromadb`. The semantic/deployed profile.

    Chroma handles the on-disk index; this class is responsible for making its output mean the same
    thing as the in-memory store's. Where Chroma is approximate, this adapter is explicit about it
    rather than letting an approximate answer look exact.
    """

    name = "chroma"

    _COLLECTION = "rag_academic_assistant"

    def __init__(self, persist_path: str | Path) -> None:
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as exc:
            raise ChromaUnavailable(
                "chromadb is not installed; the in-memory store is the persistence fallback"
            ) from exc

        self._persist_path = Path(persist_path)
        try:
            self._client = chromadb.PersistentClient(
                path=str(self._persist_path),
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self._COLLECTION, metadata={"hnsw:space": "cosine"}
            )
            # Chroma's HNSW search is approximate: it visits `search_ef` candidates rather
            # than all of them, so a tied or near-tied chunk can be missed. Setting
            # search_ef generously makes the search effectively exhaustive at the
            # corpus sizes this project targets, which is what lets the two stores agree.
            # It is recorded rather than hidden -- see Architecture section 8, which
            # states that exact top-k membership is not guaranteed at large scale.
            self._relax_search_depth()
        except Exception as exc:  # noqa: BLE001 - surfaced as a degradation, not a crash
            raise ChromaUnavailable(
                f"could not open the Chroma store at {self._persist_path}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        self._chunks: dict[str, EvidenceChunk] = {}
        self._score_fn: Any = None
        self._lock = threading.Lock()
        self._reload_cache()

    @property
    def persist_path(self) -> Path:
        return self._persist_path

    def set_similarity(self, score_fn: Any, scorer_name: str) -> None:
        self._score_fn = score_fn
        self._scorer_name = scorer_name

    def _relax_search_depth(self) -> None:
        """Raise HNSW's candidate list so top-k is exhaustive at this corpus size.

        Chroma's default `search_ef` visits only a slice of the index, so with many tied or
        near-tied scores it can return a *different* top-k than an exact search would. Raising
        the depth removes the discrepancy for corpora of this size; it does not make the algorithm
        exact in general, and [Architecture 8](../../docs/04_SYSTEM_ARCHITECTURE.md#8-determinism)
        records that honestly. If the underlying API rejects the setting, the store still works --
        it just inherits Chroma's approximation, so this is best-effort by design.
        """
        try:
            self._collection.modify(
                metadata={"hnsw:space": "cosine", "hnsw:search_ef": SEARCH_EF}
            )
        except Exception:  # noqa: BLE001 - approximation is documented, not fatal
            return None

    def _reload_cache(self) -> None:
        """Mirror the stored chunks into memory.

        Citations need filename and page, and re-deriving them would mean re-reading every PDF on
        every query. The store therefore keeps the chunk metadata it needs, rebuilt from the
        persisted collection on construction.
        """
        stored = self._collection.get(include=["metadatas", "documents"])
        self._chunks = {}
        for chunk_id, metadata, document in zip(
            stored["ids"], stored["metadatas"] or [], stored["documents"] or [], strict=True
        ):
            if metadata is None:
                continue
            self._chunks[chunk_id] = EvidenceChunk(
                chunk_id=chunk_id,
                source_id=str(metadata.get("source_id", "")),
                filename=str(metadata.get("filename", "")),
                page_number=int(metadata.get("page_number", 1)),
                chunk_index_in_page=int(metadata.get("chunk_index_in_page", 0)),
                text=document or "",
            )

    # -- VectorStore ----------------------------------------------------------

    def add(self, chunks: list[EvidenceChunk], vectors: Any) -> None:
        if len(chunks) != row_count(vectors):
            raise VectorStoreError(
                f"chunk/vector length mismatch: {len(chunks)} chunks, {row_count(vectors)} vectors"
            )
        if not chunks:
            return
        with self._lock:
            # upsert, not add: re-indexing the same file must not duplicate (EC-15).
            self._collection.upsert(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=_dense_rows(vectors).tolist(),
                documents=[chunk.text for chunk in chunks],
                metadatas=[
                    {
                        "source_id": chunk.source_id,
                        "filename": chunk.filename,
                        "page_number": chunk.page_number,
                        "chunk_index_in_page": chunk.chunk_index_in_page,
                    }
                    for chunk in chunks
                ],
            )
            self._chunks.update({chunk.chunk_id: chunk for chunk in chunks})

    def query(self, query_vector: Any, top_k: int) -> list[RetrievalResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if self._score_fn is None:
            raise VectorStoreError("no similarity function installed")
        total = self._collection.count()
        if total == 0:
            return []
        limit = min(top_k, total)

        # Over-fetch, then rank the candidates ourselves. Chroma's own ordering is
        # approximate and its tie ordering is arbitrary; re-ranking a wider candidate
        # set with our deterministic tie-break is what makes the label on a score
        # mean the same thing here as in the in-memory store.
        candidates_wanted = min(total, max(limit * CANDIDATE_OVERSAMPLE, limit))
        found = self._collection.query(
            query_embeddings=[_dense_rows(query_vector).ravel().tolist()],
            n_results=candidates_wanted,
            include=["embeddings"],
        )
        candidate_ids = found["ids"][0] if found["ids"] else []
        candidates = [self._chunks[cid] for cid in candidate_ids if cid in self._chunks]
        if not candidates:
            return []

        # Re-score with the backend's own function so a Chroma score and an in-memory
        # score mean the same number.
        candidate_vectors = np.asarray(found["embeddings"][0], dtype=np.float32)
        scores = self._score_fn(query_vector, candidate_vectors)
        scored = [(float(score), chunk) for score, chunk in zip(scores, candidates, strict=True)]
        return _sorted_results(scored, self._scorer_name, limit)

    def count(self) -> int:
        return self._collection.count()

    def delete_document(self, source_id: str) -> int:
        with self._lock:
            doomed = [cid for cid, chunk in self._chunks.items() if chunk.source_id == source_id]
            if not doomed:
                return 0
            self._collection.delete(ids=doomed)
            for chunk_id in doomed:
                self._chunks.pop(chunk_id, None)
            return len(doomed)

    def persist(self) -> None:
        """No-op: `chromadb.PersistentClient` writes on every mutation.

        Kept so both stores satisfy the same protocol, and so a future backend that needs an
        explicit flush has an obvious place to put it.
        """
        return None

    def stored_texts(self) -> list[str]:
        """Every chunk text currently held, in insertion order.

        Exists so a restarted TF-IDF backend can rebuild its vocabulary without re-reading the
        PDFs. That rebuild is a lexical fit, not re-embedding: it produces the identical
        vocabulary deterministically, and it is what lets a second process query a persisted
        index at all (EC-15). MiniLM does not need this -- its weights are on disk either way.
        """
        documents = self._collection.get(include=["documents"])["documents"] or []
        return [document or "" for document in documents]


def build_vector_store(name: str, *, persist_path: str | Path | None = None) -> VectorStore:
    """Construct a store by name. The only place the string choice is interpreted."""
    if name == "memory":
        return InMemoryVectorStore()
    if name == "chroma":
        if persist_path is None:
            raise ValueError("the chroma store requires a persist_path")
        return ChromaVectorStore(persist_path)
    raise ValueError(f"unknown vector store: {name!r}")
