"""Test-only shim exposing `app.py`'s pure helpers without a Streamlit runtime.

`app.py` is a Streamlit script: importing it normally would execute the whole UI. This module loads
its source, drops the `main()` call, and executes the rest in a namespace of its own, so tests can
call `escape`, `chip`, `RECOVERY` and friends directly.

Nothing here is imported by the application. It exists so the UI's pure logic can be tested in a
normal process, rather than being verified only by reading it or by driving a browser.

`main()` is stripped textually rather than by mocking Streamlit. If the module grew a second
top-level side effect, this shim would execute it -- loudly, during a test -- rather than hiding it.
"""

from __future__ import annotations

import types
from pathlib import Path

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"

_NAMESPACE: types.ModuleType | None = None


def load() -> types.ModuleType:
    """Load `app.py`'s definitions without running the UI. Cached across tests."""
    global _NAMESPACE
    if _NAMESPACE is not None:
        return _NAMESPACE

    source = APP_PATH.read_text("utf-8")
    body = source.split('if __name__ == "__main__":')[0]

    module = types.ModuleType("app_under_test")
    module.__file__ = str(APP_PATH)
    # Give the module a place to import from, so `from src.models import ...` resolves the same way
    # it does when Streamlit runs the file for real.
    module.__package__ = ""
    exec(compile(body, str(APP_PATH), "exec"), module.__dict__)  # noqa: S102 - test-only
    _NAMESPACE = module
    return module


def __getattr__(name: str):
    """Expose `app_under_test.escape` and friends without re-execing on every access."""
    return getattr(load(), name)


def make_response():
    """A small `AnswerResponse` for exercising the UI's rendering helpers."""
    from src.models import (
        AnswerResponse,
        Claim,
        CitationRef,
        GeneratedAnswer,
        QueryMetrics,
        RetrievalResult,
        ClaimVerification,
        EvidenceChunk,
        VerificationSummary,
    )

    chunks = [
        EvidenceChunk(
            chunk_id="chk_a", source_id="doc_a", filename="evidence.pdf",
            page_number=1, chunk_index_in_page=0,
            text="Chroma persists embeddings on the local filesystem.",
        ),
        EvidenceChunk(
            chunk_id="chk_b", source_id="doc_a", filename="evidence.pdf",
            page_number=2, chunk_index_in_page=0,
            text="Cosine similarity measures relatedness between vectors.",
        ),
    ]
    retrieved = tuple(
        RetrievalResult(rank=i + 1, chunk=c, relevance_score=0.4 - i * 0.1, backend="tfidf")
        for i, c in enumerate(chunks)
    )
    claims = tuple(
        Claim(
            claim_id=f"clm_{i}",
            text=c.text,
            markers=(CitationRef(source_id=c.source_id, page_number=c.page_number,
                                 raw=f"S{i + 1}, p.{c.page_number}", resolved=True),),
            position=i,
        )
        for i, c in enumerate(chunks)
    )
    answer = GeneratedAnswer(
        text=" ".join(f"{c.text} [{c.markers[0].raw}]" for c in claims),
        claims=claims,
        generator="extractive",
    )
    verifications = tuple(
        ClaimVerification(
            claim_id=claim.claim_id, claim_text=claim.text, label="Verified",
            support_score=0.8, similarity=0.8, overlap=0.8, evidence=chunk,
            relevance_score=0.4 - i * 0.1, reason="supported",
            explanation="Passed the check. This means correspondence, not proof.",
        )
        for i, (claim, chunk) in enumerate(zip(claims, chunks, strict=True))
    )
    return AnswerResponse(
        question="What does Chroma persist?",
        answer=answer,
        retrieved=retrieved,
        verifications=verifications,
        summary=VerificationSummary(
            verified=2, needs_review=0, unsupported=0, uncited=0, unresolved_refs=0,
            worst_support=0.8, abstained=False,
        ),
        metrics=QueryMetrics(
            embed_ms=1.0, retrieve_ms=1.0, generate_ms=1.0, verify_ms=2.0,
            total_ms=5.0, backend="tfidf", store="memory", generator="extractive",
        ),
    )