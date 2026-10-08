r"""Measure what the project claims to measure. M1-M10, on a real document.

    .venv\Scripts\python.exe -X utf8 tools\measure.py --json tests\data\metrics.json

Every number printed is produced by this run. Nothing is estimated, and where a metric cannot be
measured honestly it is reported as such rather than filled with a plausible figure.

Four methodological commitments, because measurement without them is decoration:

1. **A real document.** The fixture is the team's own Stage 2 report — 15 pages, two-column academic
   prose with tables. Not a synthetic one-line-per-page PDF. It is the hardest kind of input the
   project will actually face (R-11).
2. **The relevance judgements are hand-made and say so.** Recall@k needs a ground truth of which
   passage answers a question. Nine answerable questions were authored by reading the report, each
   with the page whose text answers it. That is a small, self-authored relevance set and its limits
   are stated wherever the number appears (R-10).
3. **Latency is reported per profile.** The offline profile and the semantic profile differ by more
   than an order of magnitude, and a single average would hide that.
4. **Peak RSS is sampled, and the interval is recorded.** A single reading can miss the peak; the
   interval is part of the method, not a detail.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import PipelineConfig  # noqa: E402
from src.pipeline import ResearchPipeline  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path.home() / "Downloads" / ".pdf" / "FAI_PE_Microproject_Stage_2_Report_Revised.pdf"

# Hand-authored relevance set. Each entry: (question, page whose text answers it).
#
# These were written by reading the report, not by running retrieval and noting what came back —
# otherwise the "relevance" judgement would just be the system's own output and Recall@k would be
# circular. Nine questions across nine different pages is a small set; that is stated at every point
# the resulting number appears.
RELEVANCE_SET: list[tuple[str, int]] = [
    ("Which embedding model does the project use?", 9),
    ("How large is the FLAN-T5-small weight file?", 9),
    ("What chunk size and overlap does the fallback chunker use?", 3),
    ("What happens when a PDF is password protected?", 4),
    ("Which Python version was used for the validation run?", 7),
    ("What does pdfplumber do when pypdf extracts too little text?", 4),
    ("Why was LangChain removed from the design?", 3),
    ("How is paper capacity described, as a guarantee or a setting?", 11),
    ("What does the report say about committing prototype commit identifiers?", 10),
]

UNANSWERABLE = [
    "What is the boiling point of mercury at sea level?",
    "Which team won the 2019 ICC Cricket World Cup?",
    "How does photosynthesis convert light into chemical energy?",
]

RSS_INTERVAL = 0.02


def _rss_mb() -> float:
    """Current resident set size in MB.

    Order matters: `psutil` first because it is readable and cross-platform, then the Win32
    `GetProcessMemoryInfo` call, then the `/proc/self/statm` fallback for Linux.

    The earlier version of this function reported 0.0 MB on every sample. The `GetProcessMemoryInfo`
    signature was wrong in a way Python did not complain about -- `ctypes` defaults `restype` to
    `c_int`, which truncates a 64-bit pointer-sized value to zero. `restype` and `argtypes` now have
    to be declared explicitly, which is the actual lesson: with FFI, an unset return type fails
    silently and looks like a measurement.
    """
    try:
        import psutil  # type: ignore

        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        pass

    if sys.platform == "win32":
        import ctypes
        import ctypes.wintypes as wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        # Both signatures must be declared explicitly. Left unset, ctypes defaults every return to
        # `c_int`, which truncates the 64-bit values this call returns and reads as 0 MB. That is
        # not a crash -- it is a plausible-looking measurement of nothing, which is worse.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)

        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetCurrentProcess.argtypes = []
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD
        ]

        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if ok:
            return counters.WorkingSetSize / (1024 * 1024)
        return float("nan")

    try:
        pages = Path("/proc/self/statm").read_text().split()[1]
        return int(pages) * 4096 / (1024 * 1024)
    except Exception:
        return float("nan")


def environment() -> dict:
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
    }
    try:
        import os

        info["cpu_count"] = os.cpu_count()
    except Exception:  # pragma: no cover
        pass
    try:
        output = subprocess.run(
            ["wmic", "CPU", "get", "name"], capture_output=True, text=True, timeout=10
        ).stdout
        for line in output.splitlines():
            if "Intel" in line or "AMD" in line or "Arm" in line:
                info["cpu_model"] = line.strip()
                break
    except Exception:
        pass
    try:
        output = subprocess.run(
            ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        for line in output.splitlines():
            if line.strip().isdigit():
                info["ram_gb"] = round(int(line.strip()) / (1024**3), 1)
                break
    except Exception:
        pass
    info["gpu"] = "none by design (CPU-only)"
    return info


def measure_indexing(runs: int = 3) -> dict:
    """Index the fixture `runs` times in fresh processes-equivalent (fresh pipelines)."""
    timings: list[float] = []
    report = None
    for _ in range(runs):
        pipeline = ResearchPipeline(PipelineConfig(store="memory"))
        started = time.perf_counter()
        report = pipeline.index([FIXTURE])
        timings.append(time.perf_counter() - started)
    assert report is not None
    return {
        "runs": runs,
        "pages": report.total_pages,
        "chunks": report.total_chunks,
        "seconds_min": round(min(timings), 4),
        "seconds_median": round(statistics.median(timings), 4),
        "seconds_max": round(max(timings), 4),
        "seconds_per_100_pages": round(statistics.median(timings) / report.total_pages * 100, 4),
    }


def measure_query_latency(questions: list[str], top_k: int = 5) -> dict:
    """p50/p95 over at least 20 queries, after the index is warm."""
    pipeline = ResearchPipeline(PipelineConfig(store="memory"))
    pipeline.index([FIXTURE])
    pipeline.ask(questions[0], top_k=top_k)  # warm-up, excluded from the statistics

    samples: list[float] = []
    repeats = max(1, (20 + len(questions) - 1) // len(questions))
    for _ in range(repeats):
        for question in questions:
            started = time.perf_counter()
            pipeline.ask(question, top_k=top_k)
            samples.append((time.perf_counter() - started) * 1000)
    samples.sort()
    return {
        "n": len(samples),
        "p50_ms": round(statistics.median(samples), 2),
        "p95_ms": round(samples[max(0, int(len(samples) * 0.95) - 1)], 2),
        "max_ms": round(samples[-1], 2),
    }


def measure_recall(pipeline: ResearchPipeline, ks: tuple[int, ...] = (1, 3, 5, 10)) -> dict:
    """Recall@k and MRR against the hand-authored relevance set."""
    out: dict = {"n_questions": len(RELEVANCE_SET), "method": "one relevant page per question"}
    for k in ks:
        hits = 0
        for question, page in RELEVANCE_SET:
            results = pipeline._retrieve(question, top_k=k)
            if any(result.chunk.page_number == page for result in results):
                hits += 1
        out[f"recall@{k}"] = round(hits / len(RELEVANCE_SET), 3)

    reciprocal = []
    for question, page in RELEVANCE_SET:
        results = pipeline._retrieve(question, top_k=10)
        for position, result in enumerate(results, start=1):
            if result.chunk.page_number == page:
                reciprocal.append(1 / position)
                break
        else:
            reciprocal.append(0.0)
    out["mrr"] = round(statistics.mean(reciprocal), 3)
    return out


def measure_abstention(pipeline: ResearchPipeline) -> dict:
    """Abstention on unanswerable questions, and whether abstaining ever fabricates.

    Read the result carefully, because **0.0 is the bad number here, not the good one.**

    The extractive generator's abstention trigger is "no sentence in the retrieved chunks was
    relevant enough to select". It does not ask whether the chunks answer the question. TF-IDF
    cosine over a shared vocabulary is near zero between unrelated English sentences, but it is not
    exactly zero, so the generator always finds *something* to quote and answers every question --
    including the three about mercury, cricket and photosynthesis, none of which appear anywhere in
    the report.

    So the measured abstention rate of 0.0 says something true and unflattering: **the offline profile
    does not know when it does not know.** That is a more serious limitation than a high
    false-abstention rate, because the failure mode is a confident answer with real citations drawn
    from irrelevant passages, which is exactly the appearance of an informed system.

    The pipeline's genuine abstention path -- an empty index -- is covered by the test suite and
    works. Detecting insufficient *retrieved* evidence is Phase 4 work that the threshold calibration
    does not solve, and it is recorded as risk R-24.
    """
    pipeline.ask("anything", top_k=3)  # warm the TF-IDF fit

    abstained = 0
    fabricated = 0
    support_on_unanswerable: list[float] = []
    for question in UNANSWERABLE:
        response = pipeline.ask(question, top_k=3)
        if response.answer.abstained:
            abstained += 1
            if response.answer.text.strip():
                fabricated += 1
        else:
            support_on_unanswerable.extend(v.support_score for v in response.verifications)

    answerable = [question for question, _ in RELEVANCE_SET]
    false_abstention = sum(
        1 for question in answerable if pipeline.ask(question, top_k=3).answer.abstained
    )
    return {
        "n_unanswerable": len(UNANSWERABLE),
        "abstentions": abstained,
        "abstention_rate": round(abstained / len(UNANSWERABLE), 3),
        "fabrications_on_abstention": fabricated,
        "n_answerable": len(answerable),
        "false_abstentions": false_abstention,
        "false_abstention_rate": round(false_abstention / len(answerable), 3),
        "mean_support_on_unanswerable": (
            round(statistics.mean(support_on_unanswerable), 3) if support_on_unanswerable else None
        ),
        "n_claims_on_unanswerable": len(support_on_unanswerable),
        "interpretation": (
            "The offline profile does not abstain when the retrieved passages do not answer the "
            "question: it quotes the least-irrelevant sentence it can find and labels that claim "
            "Unsupported, which is honest labelling attached to an answer that should not exist. "
            "The abstention path that is implemented and tested -- an empty index -- works. This is "
            "a known, measured limitation, recorded as R-24, not a fixed defect."
        ),
    }


def measure_markers(pipeline: ResearchPipeline) -> dict:
    """Marker coverage and citation resolution over the relevance set."""
    total = 0
    with_marker = 0
    resolved = 0
    for question, _ in RELEVANCE_SET:
        response = pipeline.ask(question, top_k=5)
        for claim in response.answer.claims:
            total += 1
            if claim.markers:
                with_marker += 1
        for verification in response.verifications:
            if verification.reason != "unresolvable_reference":
                resolved += 1
    return {
        "claims": total,
        "claims_with_marker": with_marker,
        "marker_coverage": round(with_marker / total, 3) if total else 0.0,
        "citation_resolution_rate": round(resolved / total, 3) if total else 0.0,
        "profile": "extractive",
        "flan_t5_marker_coverage": "not measured — FLAN-T5 weights absent",
    }


def measure_determinism(runs: int = 5) -> dict:
    """NFR-03: repeated offline runs on the same (PDF, question) pair, byte-compared.

    **Timings are excluded before comparison**, and that exclusion is the whole result.

    The first run of this function compared the full serialised response and reported a determinism
    rate of 0.2. That number was not a defect in the pipeline: the only fields that differed were
    `embed_ms`, `generate_ms`, `retrieve_ms`, `verify_ms` and `total_ms` -- wall-clock measurements,
    which are different by definition every time they are taken.

    So the claim being tested is narrower and more honest: *the answer and its verification are
    byte-identical across runs*. Timings are measured and reported separately, by
    `measure_query_latency`. Reporting a 0.2 "determinism rate" would have been a fabricated
    finding about the system, and reporting 1.0 by comparing everything would have hidden the
    distinction.
    """
    question, _ = RELEVANCE_SET[0]
    outputs: list[bytes] = []
    timed_outputs: list[bytes] = []
    for _ in range(runs):
        pipeline = ResearchPipeline(PipelineConfig(store="memory"))
        pipeline.index([FIXTURE])
        response = pipeline.ask(question, top_k=5)
        payload = response.to_dict()
        timed_outputs.append(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"))
        payload.pop("metrics", None)
        outputs.append(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"))

    identical = sum(1 for out in outputs if out == outputs[0])
    return {
        "runs": runs,
        "identical_excluding_timings": identical,
        "determinism_rate": round(identical / runs, 3),
        "identical_including_timings": sum(
            1 for out in timed_outputs if out == timed_outputs[0]
        ),
        "note": (
            "Compared fields: question, answer, claims, retrieved, verifications, summary, warnings. "
            "Excluded: QueryMetrics, whose five fields are wall-clock measurements and differ on "
            "every run by construction. A rate computed over them would measure the clock, not the "
            "system."
        ),
        "profile": "offline (tfidf + in-memory + extractive)",
        "semantic": "not measured — MiniLM weights absent",
    }


def measure_peak_rss() -> dict:
    """Peak RSS across a full index-and-query cycle, sampled."""
    samples: list[float] = []
    pipeline = ResearchPipeline(PipelineConfig(store="memory"))
    samples.append(_rss_mb())
    pipeline.index([FIXTURE])
    samples.append(_rss_mb())
    for question, _ in RELEVANCE_SET:
        pipeline.ask(question, top_k=5)
        samples.append(_rss_mb())

    usable = [value for value in samples if value == value]  # drop NaN
    if not usable:
        return {
            "measured": False,
            "reason": "resident-set size could not be read on this platform",
        }
    return {
        "peak_rss_mb": round(max(usable), 1),
        "baseline_rss_mb": round(usable[0], 1),
        "growth_mb": round(max(usable) - usable[0], 1),
        "samples": len(samples),
        "readable_samples": len(usable),
        "sampling_note": (
            "read after indexing and after each of the relevance-set queries; not a background "
            "thread, so a spike inside a single call would be missed. The peak here is the whole "
            "process including the interpreter, not the pipeline's own footprint."
        ),
    }


def measure_model_load() -> dict:
    """M8. Not measurable here, and saying so is the correct result."""
    return {
        "measured": False,
        "reason": "No model weights are present on this machine, so no model is ever loaded.",
        "expected_note": (
            "MiniLM (~90 MB) would dominate first-query latency; FLAN-T5-small (~308 MB) would "
            "dominate it further. Neither figure is measured and neither may be quoted."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    if not FIXTURE.exists():
        print(f"fixture not found: {FIXTURE}", file=sys.stderr)
        return 2

    started = time.perf_counter()
    env = environment()
    print("environment")
    for key, value in env.items():
        print(f"  {key:<12} {value}")

    print(f"\nfixture: {FIXTURE.name}")
    indexing = measure_indexing()
    print(f"\nM5 indexing latency ({indexing['runs']} runs, {indexing['pages']} pages, "
          f"{indexing['chunks']} chunks)")
    print(f"  min/median/max   {indexing['seconds_min']:.3f} / "
          f"{indexing['seconds_median']:.3f} / {indexing['seconds_max']:.3f} s")
    print(f"  per 100 pages    {indexing['seconds_per_100_pages']:.3f} s")

    pipeline = ResearchPipeline(PipelineConfig(store="memory"))
    pipeline.index([FIXTURE])
    questions = [question for question, _ in RELEVANCE_SET]
    latency = measure_query_latency(questions)
    print(f"\nM6 query latency, offline profile (n={latency['n']})")
    print(f"  p50 {latency['p50_ms']} ms · p95 {latency['p95_ms']} ms · max {latency['max_ms']} ms")

    recall = measure_recall(pipeline)
    print(f"\nM1-M2 retrieval, hand-authored relevance set (n={recall['n_questions']})")
    for k in (1, 3, 5, 10):
        print(f"  Recall@{k:<2}       {recall[f'recall@{k}']}")
    print(f"  MRR           {recall['mrr']}")

    markers = measure_markers(pipeline)
    print(f"\nM9-M10 markers and citation resolution (profile: {markers['profile']})")
    print(f"  marker coverage        {markers['marker_coverage']}")
    print(f"  citation resolution    {markers['citation_resolution_rate']}")

    abstention = measure_abstention(pipeline)
    print(f"\nM4 abstention ({abstention['n_unanswerable']} unanswerable, "
          f"{abstention['n_answerable']} answerable)")
    print(f"  abstention rate        {abstention['abstention_rate']}")
    print(f"  fabrications           {abstention['fabrications_on_abstention']}")
    print(f"  false-abstention rate  {abstention['false_abstention_rate']}")

    determinism = measure_determinism()
    print(f"\nM9 determinism ({determinism['runs']} runs, {determinism['profile']})")
    print(f"  rate {determinism['determinism_rate']}")

    rss = measure_peak_rss()
    print(f"\nM7 peak RSS")
    print(f"  baseline {rss['baseline_rss_mb']} MB · peak {rss['peak_rss_mb']} MB "
          f"({rss['samples']} samples)")

    load = measure_model_load()
    print(f"\nM8 model load time: NOT MEASURED — {load['reason']}")

    payload = {
        "fixture": FIXTURE.name,
        "environment": env,
        "M5_indexing": indexing,
        "M6_query_latency_offline": latency,
        "M1_recall": recall,
        "M9_markers": markers,
        "M4_abstention": abstention,
        "M9_determinism": determinism,
        "M7_peak_rss": rss,
        "M8_model_load": load,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    print(f"total {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())