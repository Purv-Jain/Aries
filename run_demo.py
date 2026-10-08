r"""Reproducible CLI run: index → ask → verify → exit code, with timings.

The Streamlit app is for a human. This is for a machine, a viva, and a marker who wants one command
and a defensible log. FR-48.

    .venv\Scripts\python.exe run_demo.py --pdf <path> --question "<question>"
    .venv\Scripts\python.exe run_demo.py --pdf <path> --json out.json

Exit codes are load-bearing, because a demo script that always returns 0 cannot fail visibly:

| Code | Meaning |
|---|---|
| 0 | Completed. Claims were verified; some may be `Needs Review` or `Unsupported` — that is a result, not a failure |
| 1 | A user-facing error: no document indexed, or the question was rejected |
| 2 | Bad invocation or a missing file |

Determinism is the point of `--json`: the same PDF and question produce byte-identical output, so
two runs can be diffed. That is the reproducibility claim in NFR-03, made checkable by anyone.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.models import PipelineConfig  # noqa: E402
from src.pipeline import ResearchPipeline  # noqa: E402

# The extracted report contains curly quotes and dashes. On a machine whose default encoding is
# cp1252 -- which is Windows -- printing them raises UnicodeEncodeError and kills the run partway
# through, so a demo that works in an editor fails in a terminal. Forcing UTF-8 is what makes "runs
# from a shell" true rather than "runs from an IDE".
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BANNER = "RAG Academic Research Assistant - reproducible run"


def _human(value: float) -> str:
    return f"{value:.1f}"


def run(
    pdf: Path,
    question: str,
    top_k: int,
    backend: str,
    store: str,
) -> tuple[int, str, dict | None]:
    """Index one document, ask one question, print the verified result. Returns (exit_code, text, json)."""
    config = PipelineConfig(
        embedding_backend=backend,
        store=store,
        persist_path=(Path.cwd() / ".chroma" if store == "chroma" else None),
        top_k=top_k,
    )
    pipeline = ResearchPipeline(config)

    lines: list[str] = [BANNER, "=" * len(BANNER), ""]
    lines.append(f"document   : {pdf.name}")
    lines.append(f"question   : {question}")
    lines.append(f"profile    : backend={backend} store={store} top_k={top_k}")
    lines.append("")

    started = time.perf_counter()
    report = pipeline.index([pdf])
    index_seconds = time.perf_counter() - started

    lines.append(f"indexed    : {report.total_pages} pages -> {report.total_chunks} chunks "
                 f"in {_human(index_seconds)}s")
    for document in report.documents:
        lines.append(f"             {document.display_name}: {document.page_count} pages, "
                     f"{document.chunk_count} chunks, engine={document.engine}")

    for failure in report.failures:
        lines.append(f"REJECTED   : {failure.filename} - {failure.message}")
    for warning in report.warnings:
        lines.append(f"WARNING    : {warning}")

    if report.is_empty():
        lines.append("")
        lines.append("Nothing was indexed, so no question was asked.")
        return 1, "\n".join(lines), None

    started = time.perf_counter()
    try:
        response = pipeline.ask(question, top_k=top_k)
    except ValueError as exc:
        lines.append("")
        lines.append(f"QUESTION REJECTED: {exc}")
        return 1, "\n".join(lines), None
    ask_seconds = time.perf_counter() - started

    lines.append("")
    if response.answer.abstained:
        lines.append(f"ABSTAINED  : {response.answer.abstention_reason}")
        for note in response.answer.notes:
            lines.append(f"             {note}")
        lines.append(f"timing     : ask {_human(ask_seconds * 1000)}ms")
        lines.append("")
        lines.append("No answer was produced because the retrieved evidence was insufficient.")
        return 0, "\n".join(lines), response.to_dict()

    if response.answer.degraded:
        lines.append("DEGRADED   : running on the fallback generator")

    lines.append("-" * len(BANNER))
    lines.append("ANSWER")
    lines.append("-" * len(BANNER))
    for claim in response.answer.claims:
        marker = f" [{claim.markers[0].raw}]" if claim.markers else ""
        lines.append(f"{claim.text}{marker}")
    lines.append("")

    lines.append("-" * len(BANNER))
    lines.append("VERIFICATION")
    lines.append("-" * len(BANNER))
    lines.append(response.summary.headline)
    lines.append("")
    for verification in response.verifications:
        evidence = verification.evidence
        location = (
            f"{evidence.filename} p.{evidence.page_number}" if evidence else "no resolved evidence"
        )
        lines.append(
            f"{verification.label:<14} support={verification.support_score:.2f} "
            f"(sim {verification.similarity:.2f} · overlap {verification.overlap:.2f}) "
            f"{location}"
        )
        lines.append(f"{'':<14} reason: {verification.reason}")
    lines.append("")

    if response.warnings:
        for warning in response.warnings:
            lines.append(f"WARNING    : {warning}")
        lines.append("")

    lines.append("-" * len(BANNER))
    lines.append("TIMING (milliseconds, measured)")
    lines.append("-" * len(BANNER))
    metrics = response.metrics
    lines.append(f"  embed       {_human(metrics.embed_ms)}")
    lines.append(f"  retrieve    {_human(metrics.retrieve_ms)}")
    lines.append(f"  generate    {_human(metrics.generate_ms)}")
    lines.append(f"  verify      {_human(metrics.verify_ms)}")
    lines.append(f"  total ask   {_human(metrics.total_ms)}")
    lines.append("")
    lines.append(
        "Note: support scores measure correspondence with the cited passage. They are not proof "
        "that a claim is true."
    )
    return 0, "\n".join(lines), response.to_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", required=True, type=Path, help="a text-based PDF")
    parser.add_argument(
        "--question",
        default="What technology stack is listed, and how does the system verify citations?",
        help="the question to ask",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--backend", default="tfidf", choices=["tfidf", "minilm"])
    parser.add_argument("--store", default="memory", choices=["memory", "chroma"])
    parser.add_argument("--json", type=Path, default=None, help="write the full response as JSON")
    args = parser.parse_args(argv)

    if not args.pdf.exists():
        print(f"no such file: {args.pdf}", file=sys.stderr)
        return 2
    if args.pdf.suffix.lower() != ".pdf":
        print("only PDF files are supported", file=sys.stderr)
        return 2

    started = time.perf_counter()
    code, text, payload = run(args.pdf, args.question, args.top_k, args.backend, args.store)
    print(text)
    print(f"\ntotal wall time {time.perf_counter() - started:.2f}s")

    if args.json and payload is not None:
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(f"wrote {args.json}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())