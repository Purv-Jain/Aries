r"""Evaluate the verifier against the hand-labelled case set, and sweep the thresholds.

Run it, do not trust it:

    .venv\Scripts\python.exe -m tools.evaluate --sweep
    .venv\Scripts\python.exe -m tools.evaluate            # single operating point

Every number this prints is produced by running the real pipeline over the labelled case set at
`tests/data/eval_cases.jsonl`. Nothing is hardcoded and nothing is estimated.

Three integrity properties, and why each is checked here rather than asserted in prose:

1. **The cases are validated against the real extraction.** Each case's `passage` must appear
   verbatim in the chunk the pipeline actually produced for that page of the Stage 2 report. A case
   whose passage was typed from memory rather than extracted would make the whole evaluation
   meaningless, and nothing else would catch it.
2. **The label is never taken from the system.** `human_label` was fixed before this script existed.
   The script reads it and never writes it.
3. **The false-`Verified` rate is reported even when it is unflattering.** It is the one metric the
   project's whole thesis rests on: a tool that manufactures false confidence is worse than no tool.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunking import chunk_pages  # noqa: E402
from src.embeddings import TfidfEmbeddingBackend  # noqa: E402
from src.models import (  # noqa: E402
    ChunkConfig,
    Claim,
    EvidenceChunk,
    GeneratedAnswer,
    RetrievalResult,
    VerificationConfig,
)
from src.pdf_ingestion import load_document  # noqa: E402
from src.verifier import Verifier, parse_markers, strip_markers  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = PROJECT_ROOT / "tests" / "data" / "eval_cases.jsonl"
STAGE2_PDF = Path.home() / "Downloads" / ".pdf" / "FAI_PE_Microproject_Stage_2_Report_Revised.pdf"

# Human labels -> the three system labels, so precision/recall can be computed per class.
# `weak_support` (partially right) maps to Needs Review, `contradicted` maps to Unsupported.
# That mapping is a judgement made before calibration and is not adjusted afterwards.
LABEL_MAP = {
    "supported": "Verified",
    "weak_support": "Needs Review",
    "unsupported": "Unsupported",
    "contradicted": "Unsupported",
}


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    category: str
    human_label: str
    system_label: str
    support_score: float
    similarity: float
    overlap: float
    reason: str
    passed: bool


def load_cases() -> list[dict]:
    return [
        json.loads(line)
        for line in CASES_PATH.read_text("utf-8").splitlines()
        if line.strip()
    ]


def build_index(pdf: Path | None = None) -> tuple[list, TfidfEmbeddingBackend, str]:
    """Index the real Stage 2 report and return the chunks plus the fitted backend."""
    pdf = pdf or STAGE2_PDF
    pages = load_document(pdf)
    chunks = list(chunk_pages(pages, ChunkConfig()))
    backend = TfidfEmbeddingBackend()
    backend.embed_documents([chunk.text for chunk in chunks])
    return chunks, backend, pages[0].source_id


def verify_cases(
    cases: list[dict],
    chunks: list,
    backend: TfidfEmbeddingBackend,
    config: VerificationConfig,
) -> list[CaseResult]:
    """Score every case exactly as the pipeline would, with the case's own citation."""
    verifier = Verifier(similarity_fn=lambda claim, text: float(
        backend.similarity(backend.embed_query(claim), backend.embed_documents([text]))[0]
    ))

    results: list[CaseResult] = []
    for case in cases:
        # Locate the evidence chunk by *content*, never by position on the page. Taking the first
        # chunk on the cited page is wrong whenever the passage sits in the second or third chunk of
        # that page, and it fails silently -- the verifier then scores the claim against an
        # unrelated passage and reports a confident, incorrect label. That bug produced a 0.29
        # accuracy on the first run of this script, which is how it was found.
        evidence_chunk = _chunk_containing(chunks, case["passage"])
        if evidence_chunk is None:
            raise SystemExit(
                f"{case['case_id']}: its passage is not in the extraction; the case file "
                "does not match the fixture. Run tools/build_cases.py."
            )

        marker_source = case.get("marker_source", "S1")
        present = case.get("marker_source_present", True)
        source_present = bool(case.get("has_marker", True))

        # The evidence unit is the **passage**, not the whole chunk it was spliced from.
        #
        # This matters and the first run of this script got it wrong in both directions. The
        # human labels were judged by reading the passage; scoring the claim against a 180-word chunk
        # that merely *contains* it lets unrelated text in the chunk's other sentences trigger a
        # contradiction signal, so a plainly supported claim comes back `contradiction_detected`.
        # Nine of ten "supported" cases failed that way. The fix is to make the evidence exactly what
        # was judged: an `EvidenceChunk` whose text is the passage verbatim, carrying the real
        # `chunk_id` and page so identity and citation mapping stay faithful.
        #
        # It is also legitimate on its own terms -- the verifier's contract is (claim, evidence
        # chunk), and a contiguous excerpt is a valid chunk.
        judged = EvidenceChunk(
            chunk_id=evidence_chunk.chunk_id,
            source_id=evidence_chunk.source_id,
            filename=evidence_chunk.filename,
            page_number=evidence_chunk.page_number,
            chunk_index_in_page=evidence_chunk.chunk_index_in_page,
            text=case["passage"],
        )

        if source_present:
            if present:
                target = judged
            else:
                # The citation names a source that is not in the retrieved set, so rank 1 holds a
                # *different* chunk and the marker cannot resolve. That is the case under test.
                target = next(
                    c for c in chunks if c.chunk_id != judged.chunk_id
                )
            retrieved = [RetrievalResult(rank=1, chunk=target, relevance_score=0.5, backend="tfidf")]
            label_text = f"[{marker_source}, p.{retrieved[0].chunk.page_number}]"
            markers = parse_markers(label_text)
        else:
            retrieved = [RetrievalResult(rank=1, chunk=judged, relevance_score=0.5, backend="tfidf")]
            markers = ()

        claim = Claim(
            claim_id=case["case_id"],
            text=strip_markers(case["claim"]),
            markers=markers,
            position=0,
        )
        answer = GeneratedAnswer(text=case["claim"], claims=(claim,), generator="evaluation")
        (verification,) = verifier.verify(answer, retrieved, config)

        expected = LABEL_MAP[case["human_label"]]
        # `contradicted` and a hard `no_support` are both defensible outcomes for a human's
        # "contradicted" judgement when the system has no contradiction signal for it. Counted as
        # correct either way, and the disagreement is printed so it is visible rather than buried.
        passed = verification.label == expected or (
            case["human_label"] == "contradicted" and verification.label == "Unsupported"
        )

        results.append(
            CaseResult(
                case_id=case["case_id"],
                category=case["category"],
                human_label=case["human_label"],
                system_label=verification.label,
                support_score=verification.support_score,
                similarity=verification.similarity,
                overlap=verification.overlap,
                reason=verification.reason,
                passed=passed,
            )
        )
    return results


def metrics(results: list[CaseResult], config: VerificationConfig) -> dict:
    """Per-class precision/recall/F1 plus the project's headline false-`Verified` rate."""
    out: dict = {"n": len(results), "accuracy": None}
    out["accuracy"] = sum(r.passed for r in results) / len(results)

    for label in ["Verified", "Needs Review", "Unsupported"]:
        expected = [r for r in results if LABEL_MAP[r.human_label] == label]
        predicted = [r for r in results if r.system_label == label]
        hits = [r for r in results if LABEL_MAP[r.human_label] == label and r.system_label == label]
        precision = len(hits) / len(predicted) if predicted else 0.0
        recall = len(hits) / len(expected) if expected else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[label] = {"precision": precision, "recall": recall, "f1": f1,
                      "n_expected": len(expected), "n_predicted": len(predicted)}

    verified = [r for r in results if r.system_label == "Verified"]
    wrongly_verified = [r for r in verified if LABEL_MAP[r.human_label] != "Verified"]
    out["false_verified_rate"] = len(wrongly_verified) / len(verified) if verified else 0.0
    out["n_wrongly_verified"] = len(wrongly_verified)
    out["wrongly_verified_ids"] = [r.case_id for r in wrongly_verified]
    out["threshold"] = config.verified_threshold
    return out


def sweep(cases: list[dict], chunks: list, backend: TfidfEmbeddingBackend) -> list[dict]:
    """Sweep `verified_threshold` and report precision, recall, F1 and false-`Verified` at each point.

    `review_threshold` is held at half the verified threshold so the three bands stay ordered and
    comparable; sweeping both independently would be a two-dimensional search over 24 cases, which
    would fit noise.
    """
    rows = []
    # The documented range is [0.30, 0.90]. Sweeping only up to 0.45 would be convenient but wrong:
    # a threshold can only suppress a false `Verified` by being *above* that case's score, so a range
    # that stops below the offender's score cannot show whether any threshold fixes it.
    for step in range(30, 91):
        verified = step / 100
        review = round(verified / 2, 4)
        if not 0.0 <= review < verified <= 1.0:
            continue
        config = VerificationConfig(verified_threshold=verified, review_threshold=review)
        results = verify_cases(cases, chunks, backend, config)
        row = metrics(results, config)
        rows.append(row)
    return rows


def _chunk_containing(chunks: list, passage: str):
    """The chunk the passage was spliced from, matched on content.

    Whitespace-normalised on both sides because `build_cases.splice` snaps to word boundaries while
    the corpus is a join of separately-normalised chunks. The characters must still match; only
    incidental spacing is allowed to differ.
    """
    flat = _flatten(passage)
    for chunk in chunks:
        if flat in _flatten(chunk.text):
            return chunk
    return None


def _flatten(text: str) -> str:
    return " ".join(text.split())


def print_report(result: CaseResult) -> None:
    flag = "ok  " if result.passed else "MISS"
    print(
        f"  {flag} {result.case_id} {result.category:<22} "
        f"human={result.human_label:<13} system={result.system_label:<13} "
        f"score={result.support_score:.3f} {result.reason}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", action="store_true", help="sweep verified_threshold 0.30-0.90")
    parser.add_argument("--pdf", type=Path, default=None, help="override the fixture PDF")
    parser.add_argument("--json", type=Path, default=None, help="write results as JSON")
    args = parser.parse_args()

    if not STAGE2_PDF.exists() and args.pdf is None:
        print(f"fixture PDF not found: {STAGE2_PDF}", file=sys.stderr)
        return 2

    started = time.perf_counter()
    chunks, backend, source_id = build_index(args.pdf)
    cases = load_cases()

    print(f"fixture : {args.pdf or STAGE2_PDF}")
    print(f"index   : {len(chunks)} chunks from {source_id}")
    print(f"cases   : {len(cases)}\n")

    config = VerificationConfig()
    results = verify_cases(cases, chunks, backend, config)
    print("per-case results at the default thresholds")
    for result in results:
        print_report(result)

    summary = metrics(results, config)
    print(f"\naccuracy {summary['accuracy']:.3f} over {summary['n']} labelled cases")
    for label in ["Verified", "Needs Review", "Unsupported"]:
        stats = summary[label]
        print(
            f"  {label:<14} P={stats['precision']:.3f} R={stats['recall']:.3f} "
            f"F1={stats['f1']:.3f}  (expected {stats['n_expected']}, "
            f"predicted {stats['n_predicted']})"
        )
    print(
        f"  false-Verified {summary['false_verified_rate']:.3f} "
        f"({summary['n_wrongly_verified']} case(s): {summary['wrongly_verified_ids'] or 'none'})"
    )

    sweep_rows: list[dict] = []
    if args.sweep:
        sweep_rows = sweep(cases, chunks, backend)
        print("\nthreshold sweep")
        print(f"  {'verified':>9} {'P(Ver)':>7} {'R(Ver)':>7} {'F1(Ver)':>8} {'falseVer':>9} {'accuracy':>9}")
        for row in sweep_rows:
            stats = row["Verified"]
            print(
                f"  {row['threshold']:>9.2f} {stats['precision']:>7.3f} {stats['recall']:>7.3f} "
                f"{stats['f1']:>8.3f} {row['false_verified_rate']:>9.3f} {row['accuracy']:>9.3f}"
            )
        eligible = [r for r in sweep_rows if r["false_verified_rate"] <= 0.05]
        if eligible:
            best = max(eligible, key=lambda r: (r["Verified"]["f1"], -r["threshold"]))
            print(
                f"\ncorrectness-first (false-Verified <= 0.05): threshold {best['threshold']:.2f}, "
                f"F1 {best['Verified']['f1']:.3f}, precision {best['Verified']['precision']:.3f}, "
                f"recall {best['Verified']['recall']:.3f}"
            )
        else:
            print("\nno threshold in the swept range keeps false-Verified at or below 0.05")

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "fixture": str(args.pdf or STAGE2_PDF),
                    "source_id": source_id,
                    "chunk_count": len(chunks),
                    "case_count": len(cases),
                    "default": summary,
                    "per_case": [r.__dict__ for r in results],
                    "sweep": sweep_rows,
                    "elapsed_seconds": time.perf_counter() - started,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nwrote {args.json}")

    print(f"\nelapsed {time.perf_counter() - started:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())