"""Embedding backends: one protocol, two very different implementations.

The pipeline never knows which one it is holding. That is the whole point of the
split described in [ADR-0005](../../docs/05_TECH_STACK_AND_ADRS.md): the offline
profile and the semantic profile differ in a backend object, not in the pipeline
above it, so the fallback is testable rather than aspirational.

| | `TfidfEmbeddingBackend` | `MiniLMEmbeddingBackend` |
|---|---|---|
| Needs a download | No | Yes, once (~90 MB) |
| Needs a network | No | Only on first load |
| Vectors | sparse TF-IDF, fitted on the corpus | dense 384-dim, L2-normalised |
| Similarity | cosine on non-negative weights -> already `[0, 1]` | cosine in `[-1, 1]` -> rescaled `(s + 1) / 2` |
| Role | the **default**, and the test profile | opt-in, degrades loudly |

The asymmetry in the similarity column is not sloppiness. It is a real property of
the two backends and it is documented in
[Architecture 5.2](../../docs/04_SYSTEM_ARCHITECTURE.md#52-what-each-term-is-precisely); it is the
reason each backend owns its own `similarity()` instead of the store owning one.

Nothing here imports `torch` or `sentence_transformers` at module level. The default test suite
must stay green with no model weights on disk, and an import-time dependency would quietly undo
that guarantee.
"""

from __future__ import annotations

import os
from typing import Any, Protocol, runtime_checkable

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

__all__ = [
    "EmbeddingBackendUnavailable",
    "EmbeddingBackend",
    "TfidfEmbeddingBackend",
    "MiniLMEmbeddingBackend",
    "build_embedding_backend",
    "row_count",
]

# TF-IDF token pattern: words and numbers, single characters dropped so that "a"
# and stray symbols do not become dimensions. Fixed deliberately -- an unfitted
# vocabulary is not reproducible, and reproducibility is the whole fallback promise.
_TOKEN_PATTERN = r"(?u)\b[a-zA-Z][a-zA-Z0-9]+\b"

MINILM_DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MINILM_DIMENSION = 384


class EmbeddingBackendUnavailable(RuntimeError):
    """The backend cannot run here.

    Raised rather than returning empty vectors, because a silently empty embedding
    looks exactly like a document with no content, and the index would then report
    a corpus it does not have.
    """


def row_count(vectors: Any) -> int:
    """How many stored rows a matrix holds, sparse or dense.

    ``len()`` is ambiguous on a SciPy sparse matrix and raises ``TypeError``. Since the backends
    and the stores both need this, it lives here as one function rather than as a ``shape[0]``
    scattered across five call sites, each of which could get it subtly wrong.
    """
    if vectors is None:
        return 0
    shape = getattr(vectors, "shape", None)
    if shape is None:
        return 0
    return int(shape[0])


@runtime_checkable
class EmbeddingBackend(Protocol):
    """What the pipeline requires of an embedder.

    ``similarity`` returns one score per stored vector, already normalised to
    `[0, 1]`. Each backend owns that normalisation because the two families do not
    produce scores on the same scale, and moving the rescale into a shared place
    would be how the two scores eventually get conflated.
    """

    name: str

    def embed_documents(self, texts: list[str]) -> Any: ...

    def embed_query(self, text: str) -> Any: ...

    def similarity(self, query_vector: Any, stored_vectors: Any) -> np.ndarray: ...

    @property
    def dimension(self) -> int: ...


class TfidfEmbeddingBackend:
    """Deterministic lexical backend. No download, no network, no model file.

    Fits its vocabulary on the documents it is given and keeps the fitted vectoriser,
    because a query vector is only comparable to document vectors built from the same
    vocabulary. A fresh unfitted vectoriser per query would return nonsense.
    """

    name = "tfidf"

    def __init__(self) -> None:
        self._vectoriser = TfidfVectorizer(
            token_pattern=_TOKEN_PATTERN,
            lowercase=True,
            norm="l2",
            sublinear_tf=True,
        )
        self._fitted = False

    @property
    def dimension(self) -> int:
        if not self._fitted:
            return 0
        return len(self._vectoriser.vocabulary_)

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def fit(self, texts: list[str]) -> None:
        """Fit the vocabulary. Refitting is deliberate and happens only on re-index."""
        self._vectoriser.fit(texts)
        self._fitted = True

    def embed_documents(self, texts: list[str]) -> Any:
        if not texts:
            return sparse.csr_matrix((0, max(self.dimension, 0)), dtype=np.float64)
        if not self._fitted:
            self.fit(texts)
        return self._vectoriser.transform(texts)

    def embed_query(self, text: str) -> Any:
        if not self._fitted:
            raise EmbeddingBackendUnavailable(
                "the TF-IDF backend has not been fitted; index at least one document first"
            )
        return self._vectoriser.transform([text])

    def similarity(self, query_vector: Any, stored_vectors: Any) -> np.ndarray:
        """Cosine similarity, which for non-negative TF-IDF weights is already `[0, 1]`.

        No rescale is applied here, unlike the semantic backend. Applying one would
        inflate every unrelated pair from 0.0 to 0.5 and make "shares no vocabulary"
        look like "moderately related".
        """
        if row_count(stored_vectors) == 0:
            return np.zeros(0, dtype=np.float64)
        scores = cosine_similarity(query_vector, stored_vectors).ravel()
        return np.clip(scores, 0.0, 1.0)


class MiniLMEmbeddingBackend:
    """Semantic backend. Loads lazily, and fails in a way the pipeline can act on.

    Two separate failure modes are handled, because they need different answers:

    * ``sentence_transformers`` not installed -> the optional dependency is missing.
    * weights not on disk and no network -> the download cannot happen.

    Both become `EmbeddingBackendUnavailable` with a message naming which one it was, so the
    UI can say "semantic backend unavailable, using TF-IDF" instead of a stack trace.
    """

    name = "minilm"

    def __init__(
        self,
        model_name: str = MINILM_DEFAULT_MODEL,
        *,
        local_files_only: bool = False,
        expected_dimension: int = MINILM_DIMENSION,
    ) -> None:
        self.model_name = model_name
        self._local_files_only = local_files_only
        self._expected_dimension = expected_dimension
        self._model: Any = None

    @property
    def dimension(self) -> int:
        return self._expected_dimension

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingBackendUnavailable(
                "sentence-transformers is not installed, so the semantic backend cannot run. "
                "Install it, or use the tfidf backend."
            ) from exc
        try:
            self._model = SentenceTransformer(
                self.model_name, local_files_only=self._local_files_only
            )
        except Exception as exc:  # noqa: BLE001 - any loader failure degrades the same way
            raise EmbeddingBackendUnavailable(
                f"could not load {self.model_name} "
                f"(local_files_only={self._local_files_only}): {type(exc).__name__}: {exc}"
            ) from exc
        return self._model

    def embed_documents(self, texts: list[str]) -> Any:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        model = self._load()
        # normalize_embeddings=True is what makes the dot product below a cosine,
        # and it is set explicitly rather than assumed from model defaults.
        return model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

    def embed_query(self, text: str) -> Any:
        return self.embed_documents([text])[0]

    def similarity(self, query_vector: Any, stored_vectors: Any) -> np.ndarray:
        """Cosine similarity rescaled to `[0, 1]`.

        Raw cosine on normalised embeddings is nearly always non-negative but not
        guaranteed to be, and a negative relevance score would be nonsense to a user
        and would break `RetrievalResult`'s `[0, 1]` invariant.

        **The query is reshaped to a single row first, and that is a bug fix rather than
        tidiness.** `embed_query` returns `embed_documents([text])[0]`, which is a *1-D*
        `(384,)` array, while `embed_documents` returns a 2-D `(n, 384)` matrix.
        `sklearn.metrics.pairwise.cosine_similarity` rejects a 1-D input outright, so every
        semantic query raised `ValueError: Expected 2D array, got 1D array instead`.

        The semantic retrieval path had therefore never worked, and nothing said so: the
        six `semantic`-marked tests were deselected on every run because the weights were
        absent, and the TF-IDF profile -- which returns a sparse `(1, n)` matrix from
        `embed_query` and so never trips this -- passed all 441 offline tests throughout.
        A defect can be invisible for exactly as long as nobody runs the path that contains it.

        Both 1-D and 2-D queries are accepted, so callers do not have to know which they hold.
        """
        matrix = np.asarray(stored_vectors, dtype=np.float32)
        if matrix.size == 0:
            return np.zeros(0, dtype=np.float64)
        query = np.asarray(query_vector, dtype=np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)
        raw = cosine_similarity(query, np.atleast_2d(matrix)).ravel()
        return np.clip((raw + 1.0) / 2.0, 0.0, 1.0)


def build_embedding_backend(name: str, **kwargs: Any) -> EmbeddingBackend:
    """Construct a backend by name. The only place the string choice is interpreted."""
    if name == "tfidf":
        return TfidfEmbeddingBackend()
    if name == "minilm":
        return MiniLMEmbeddingBackend(**kwargs)
    raise ValueError(f"unknown embedding backend: {name!r}")


def models_are_downloaded(model_name: str = MINILM_DEFAULT_MODEL) -> bool:
    """True when the weights are already in the local Hugging Face cache.

    Used by tests and by the UI to decide whether to *offer* the semantic profile, without
    attempting a download as a side effect of asking the question.
    """
    if os.environ.get("HF_HUB_OFFLINE") == "1":
        return False
    try:
        from huggingface_hub import try_to_load_from_cache
    except ImportError:
        return False
    hit = try_to_load_from_cache(repo_id=model_name, filename="config.json")
    return isinstance(hit, str)