r"""Rebuild `tests/data/eval_cases.jsonl` so every passage is verbatim from the fixture.

Creation rule 1 in docs/10_EVALUATION_METRICS.md says cases must be written from real extracted
passages, pasted into the case file, and that inventing plausible-looking passages is forbidden. The
first draft of the file violated that in two ways, and this script exists because the evaluation run
caught both rather than because they were noticed by eye:

* Three cases declared `passage_page: 2` while the passage is on page 3.
* Two passages were typed from memory with paraphrased punctuation and so did not match the
  extraction byte-for-byte.

Neither is a subtle data-cleaning issue: a case whose passage does not exist in the fixture makes
the whole evaluation meaningless, and nothing downstream would have said so except a suspiciously
low accuracy.

So the human judgement and the system input are separated properly. **This script never touches
`human_label`, `category` or `human_justification`** -- those are judgement, authored from reading
the passage, and they were fixed before any system run. What it does supply is the *evidence text*:
given an anchor phrase, it finds the containing chunk in the real extraction and splices the exact
characters from it.

    .venv\Scripts\python.exe -X utf8 tools/build_cases.py

Re-running it is idempotent and cannot change a label.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunking import chunk_pages  # noqa: E402
from src.pdf_ingestion import load_document  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Joined component by component, never as one r"a\b\c" literal: on POSIX a backslash is a
# legal filename character, so the literal becomes one long filename and the path never
# resolves. That bug shipped in tests/test_hardening.py and failed only on ubuntu.
CASES_PATH = PROJECT_ROOT / "tests" / "data" / "eval_cases.jsonl"
STAGE2_PDF = (
    Path.home() / "Downloads" / ".pdf" / "FAI_PE_Microproject_Stage_2_Report_Revised.pdf"
)

# The judgement layer. Keys are the existing case_ids; values are what a human decided by reading
# the passage, independently of anything the system produced.
#
# `anchor` is a distinctive phrase from the passage. It is used only to *locate* the passage in the
# extraction -- never as the passage itself. `window` is how many characters of the real chunk to
# take around the anchor.
JUDGEMENTS: dict[str, dict] = {
    "eval_01": {
        "anchor": "500 tokens vs. 500 words",
        "window": 300,
        "category": "supported_direct",
        "human_label": "supported",
        "human_justification": "The passage states the 180-word chunk size with 30-word overlap explicitly. The claim restates it.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "Stage 2 standardizes the fallback chunker to about 180 words with 30-word overlap.",
    },
    "eval_02": {
        "anchor": "PyPDF2 dependency",
        "window": 340,
        "category": "supported_direct",
        "human_label": "supported",
        "human_justification": "Both package names and their order appear verbatim in the passage.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "Stage 2 uses pypdf first and pdfplumber as a fallback.",
    },
    "eval_03": {
        "anchor": "2.1.4 Grounded Answer Generation",
        "window": 420,
        "category": "supported_direct",
        "human_label": "supported",
        "human_justification": "The passage names FLAN-T5-small and gives the student-laptop reason.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "FLAN-T5-small was chosen instead of a much larger model because the project must run on a student laptop.",
    },
    "eval_04": {
        "anchor": "Only PDF files are accepted",
        "window": 420,
        "category": "supported_direct",
        "human_label": "supported",
        "human_justification": "The passage lists each validation the ingestion layer performs, including the password case.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "The ingestion layer rejects non-PDF input and stops with a readable message on a password-protected document.",
    },
    "eval_05": {
        "anchor": "The code is divided by responsibility",
        "window": 420,
        "category": "supported_direct",
        "human_label": "supported",
        "human_justification": "The passage names pipeline.py as the only orchestration layer.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "pipeline.py is the only orchestration layer; it calls the other modules.",
    },
    "eval_06": {
        "anchor": "The safetensors weight file",
        "window": 260,
        "category": "supported_direct",
        "human_label": "supported",
        "human_justification": "The passage gives 308 MB for the FLAN-T5-small weight file.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "The safetensors weight file for FLAN-T5-small is about 308 MB.",
    },
    "eval_07": {
        "anchor": "Paper capacity",
        "window": 240,
        "category": "supported_paraphrase",
        "human_label": "supported",
        "human_justification": "Same meaning as the passage's configurable-not-guaranteed wording, in different vocabulary.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "Paper capacity is a tunable setting rather than a promise the system makes.",
    },
    "eval_08": {
        "anchor": "Fixed verification thresholds treated as proof",
        "window": 300,
        "category": "supported_paraphrase",
        "human_label": "supported",
        "human_justification": "The passage's not-proof point restated as a caution against treating similarity as correctness.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "A cosine similarity score shows semantic relatedness and should not be read as proof of correctness.",
    },
    "eval_09": {
        "anchor": "Invalid citation marker",
        "window": 280,
        "category": "supported_paraphrase",
        "human_label": "supported",
        "human_justification": "Same rule in different words: an unresolved marker becomes Unsupported.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "A citation that fails to resolve to retrieved evidence is reported as Unsupported.",
    },
    "eval_10": {
        "anchor": "No paid OpenAI",
        "window": 320,
        "category": "supported_paraphrase",
        "human_label": "supported",
        "human_justification": "The no-paid-API point restated in different words.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "The baseline design does not depend on any commercial API.",
    },
    "eval_11": {
        "anchor": "A reproducible validation run was executed",
        "window": 380,
        "category": "partial_support",
        "human_label": "weak_support",
        "human_justification": "The passage says 28 chunks; the claim says 30. Related and nearly right, but the number differs.",
        "labeller_a": "weak_support", "labeller_b": "weak_support",
        "claim": "The Level 1 document was split into 30 chunks.",
    },
    "eval_12": {
        "anchor": "A reproducible validation run was executed",
        "window": 380,
        "category": "partial_support",
        "human_label": "weak_support",
        "human_justification": "The passage says Python 3.13.5; the claim says 3.12.0. Right substance, wrong specific version.",
        "labeller_a": "weak_support", "labeller_b": "weak_support",
        "claim": "The validation run used Python 3.12.0.",
    },
    "eval_13": {
        # The extraction uses a curly apostrophe, so the anchor has to as well. Matching the
        # fixture's punctuation exactly is the whole point of this file.
        "anchor": "existing laptop, storage, electricity",
        "window": 400,
        "category": "partial_support",
        "human_label": "weak_support",
        "human_justification": "The passage is about costs and paid APIs; it never says the prototype was an IoT irrigation system. On-topic only by adjacency. The two labellers disagreed (weak_support vs unsupported); reconciled to weak_support because the passage is topically adjacent.",
        "labeller_a": "weak_support", "labeller_b": "unsupported",
        "claim": "The prototype project was built using an IoT-based smart irrigation system.",
    },
    "eval_14": {
        "anchor": "SDG relevance",
        "window": 300,
        "category": "partial_support",
        "human_label": "weak_support",
        "human_justification": "The passage reports INR 0 for the baseline, which is a stated design choice, not a measured saving. The claim converts one into the other. Scope differs.",
        "labeller_a": "weak_support", "labeller_b": "weak_support",
        "claim": "Using the local design reduced the project's API expenditure by INR 0 per paper.",
    },
    "eval_15": {
        "anchor": "Results The current automated test suite",
        "window": 400,
        "category": "unsupported_absent",
        "human_label": "unsupported",
        "human_justification": "The passage discusses test count and control flow; it says nothing about coverage.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The Stage 2 test suite achieves 87% branch coverage.",
    },
    "eval_16": {
        "anchor": "The code is divided by responsibility",
        "window": 420,
        "category": "unsupported_absent",
        "human_label": "unsupported",
        "human_justification": "On-topic (code structure) but the passage gives no line count.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The Stage 2 codebase contains 1,200 lines of production Python.",
    },
    "eval_17": {
        "anchor": "The chunk size has been reduced",
        "window": 320,
        "category": "unsupported_absent",
        "human_label": "unsupported",
        "human_justification": "The passage explains why the chunk size changed; it never claims a speedup.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The reduced chunk size makes chunking approximately four times faster than the Stage 1 configuration.",
    },
    "eval_18": {
        "anchor": "Invalid citation marker",
        "window": 280,
        "category": "contradicted",
        "human_label": "contradicted",
        "human_justification": "The passage says an invalid marker is Unsupported; the claim says it is repaired. Opposite polarity, same words.",
        "labeller_a": "contradicted", "labeller_b": "contradicted",
        "claim": "An invalid citation marker is silently repaired and re-pointed at the nearest retrieved passage.",
    },
    "eval_19": {
        "anchor": "These tests do not claim that the final semantic verifier",
        "window": 320,
        "category": "contradicted",
        "human_label": "contradicted",
        "human_justification": "The passage explicitly disclaims scientific calibration; the claim asserts it. Direct contradiction.",
        "labeller_a": "contradicted", "labeller_b": "contradicted",
        "claim": "The Stage 2 verification thresholds have been scientifically calibrated against labelled data.",
    },
    "eval_20": {
        "anchor": "The commit identifiers above belong",
        "window": 480,
        "category": "contradicted",
        "human_label": "contradicted",
        "human_justification": "The passage forbids presenting prototype commits as individual work; the claim does exactly that.",
        "labeller_a": "contradicted", "labeller_b": "contradicted",
        "claim": "Commit a6bb764 is evidence of Rishabh Jain's individual Stage 3 work.",
    },
    # -- antonym branch: R-25 -------------------------------------------------
    # Phase 7 added these after the 24-case set was found to contain no antonym pair at all, so
    # the branch was unit-tested but unmeasured against labelled data. Four cases must fire the
    # contradiction check; six must not, covering the four distinct reasons it declines:
    # the passage uses the same direction, the claim is negated, the claim is about a different
    # subject (ant_08, ant_09 -- the two that motivated the subject gate), and plain absence of
    # any antonym word.
    "ant_01": {
        "anchor": "much larger model",
        "window": 300,
        "category": "contradicted_antonym",
        "human_label": "contradicted",
        "human_justification": "The passage says a much LARGER model was rejected; the claim says a much SMALLER one was. One word inverted, meaning reversed.",
        "labeller_a": "contradicted", "labeller_b": "contradicted",
        "claim": "FLAN-T5-small was selected instead of a much smaller model because this is a microproject expected to run on a student laptop.",
    },
    "ant_02": {
        "anchor": "Smaller chunks reduce silent truncation",
        "window": 300,
        "category": "contradicted_antonym",
        "human_label": "contradicted",
        "human_justification": "The passage attributes the reduction to SMALLER chunks; the claim attributes it to LARGER chunks.",
        "labeller_a": "contradicted", "labeller_b": "contradicted",
        "claim": "Larger chunks reduce silent truncation and improve page-level evidence precision.",
    },
    "ant_03": {
        "anchor": "has been reduced from the Level 1 proposal",
        "window": 340,
        "category": "contradicted_antonym",
        "human_label": "contradicted",
        "human_justification": "The passage says the chunk size was REDUCED from the Level 1 proposal; the claim says it was INCREASED.",
        "labeller_a": "contradicted", "labeller_b": "contradicted",
        "claim": "The chunk size was increased from the Level 1 proposal so that evidence is preserved by the MiniLM embedding model.",
    },
    "ant_04": {
        "anchor": "Improves reliability for classroom evaluation",
        "window": 300,
        "category": "contradicted_antonym",
        "human_label": "contradicted",
        "human_justification": "The passage credits source markers with IMPROVING classroom reliability; the claim says skipping them DEGRADES it. Opposite direction, same metric.",
        "labeller_a": "contradicted", "labeller_b": "contradicted",
        "claim": "Skipping the source markers degrades reliability for classroom evaluation.",
    },
    "ant_05": {
        "anchor": "larger models may improve retrieval",
        "window": 320,
        "category": "supported_same_direction",
        "human_label": "supported",
        "human_justification": "Restates the passage. It contains both 'larger' and 'increase', but the claim asserts the same directions the passage does, so nothing is contradicted.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "Larger models may improve retrieval but increase download, RAM and inference time.",
    },
    "ant_06": {
        "anchor": "only practical costs",
        "window": 300,
        "category": "supported_same_direction",
        "human_label": "supported",
        "human_justification": "Restates the passage's list of practical costs.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "The only practical costs are the team's existing laptop and storage.",
    },
    "ant_07": {
        "anchor": "has been reduced from the Level 1 proposal",
        "window": 340,
        "category": "supported_negated",
        "human_label": "supported",
        "human_justification": "The passage says the size was reduced; 'was not increased' is the same fact stated with a negation. The claim must not be flagged as contradicting.",
        "labeller_a": "supported", "labeller_b": "supported",
        "claim": "The chunk size was not increased from the Level 1 proposal.",
    },
    "ant_08": {
        "anchor": "The overlap reduces the chance",
        "window": 300,
        "category": "unsupported_other_subject",
        "human_label": "unsupported",
        "human_justification": "The passage says the overlap reduces the chance of a chunk-boundary split. It says nothing about how many passages are retrieved, so the claim is unsupported \u2014 but it is NOT contradicted, because the passage takes no position on it.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The number of retrieved passages increased during indexing.",
    },
    "ant_09": {
        "anchor": "Reduces blind trust in generated references",
        "window": 300,
        "category": "unsupported_other_subject",
        "human_label": "unsupported",
        "human_justification": "The passage is about reducing blind trust in generated references. It says nothing about paid API expenditure. Unsupported, not contradicted.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The paid API expenditure increased after Stage 2.",
    },
    "ant_10": {
        "anchor": "Technology stack specifications",
        "window": 320,
        "category": "unsupported_other_subject",
        "human_label": "unsupported",
        "human_justification": "The passage is the technology-stack table. It reports no evaluation accuracy before or after Stage 2, so the claim is unsupported.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The evaluation accuracy improved after Stage 2 was completed.",
    },
    "eval_21": {
        "anchor": "PyPDF2 dependency",
        "window": 340,
        "category": "unresolvable_reference",
        "human_label": "unsupported",
        "human_justification": "The marker names a source that is not in the retrieved set. Under the project's own rule an unresolvable citation is Unsupported however plausible the sentence is.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The maintained package name is now pypdf.",
        "marker_source": "S7", "marker_source_present": False,
    },
    "eval_22": {
        "anchor": "The safetensors weight file",
        "window": 260,
        "category": "unresolvable_reference",
        "human_label": "unsupported",
        "human_justification": "The citation names an unretrieved source; the sentence is plausible but the reference does not resolve.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "Streamlit is the target user interface for the project.",
        "marker_source": "S4", "marker_source_present": False,
    },
    "eval_23": {
        "anchor": "2.1.4 Grounded Answer Generation",
        "window": 420,
        "category": "uncited_claim",
        "human_label": "unsupported",
        "human_justification": "The sentence carries no citation. An uncited factual claim cannot be Verified under the project's rule, whatever its content.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "The fallback generator ranks evidence sentences and returns the most relevant ones with source markers.",
        "has_marker": False,
    },
    "eval_24": {
        "anchor": "Only PDF files are accepted",
        "window": 420,
        "category": "uncited_claim",
        "human_label": "unsupported",
        "human_label_note": "The content would be correct against this passage, but it carries no marker, so it is uncited rather than supported.",
        "human_justification": "Uncited. This case exists to show the rule separating correctness from traceability: the sentence is true of the passage and is still not Verifiable.",
        "labeller_a": "unsupported", "labeller_b": "unsupported",
        "claim": "If a page contains very little extractable text, pdfplumber is tried as a second parser.",
        "has_marker": False,
    },
}


def _flatten(text: str) -> str:
    return " ".join(text.split())


def splice(text: str, anchor: str, window: int) -> str:
    """Return a real excerpt of `text` centred on `anchor`, snapped to word boundaries."""
    position = text.find(anchor)
    if position < 0:
        raise SystemExit(f"anchor not found in chunk: {anchor!r}")
    start = max(0, position - window // 3)
    end = min(len(text), start + window)
    start = text.rfind(" ", 0, start) + 1
    end = text.find(" ", end)
    if end < 0:
        end = len(text)
    return text[start:end].strip()


def main() -> int:
    if not STAGE2_PDF.exists():
        print(f"fixture PDF not found: {STAGE2_PDF}", file=sys.stderr)
        return 2

    pages = load_document(STAGE2_PDF)
    chunks = chunk_pages(pages)

    lines = []
    for case_id, judgement in JUDGEMENTS.items():
        # Locate the anchor inside a *single* chunk, and splice only from that chunk. Splicing from
        # the joined corpus would let a passage straddle a chunk boundary, which would then never
        # match any one chunk and would fail the verbatim check -- the first draft of this file made
        # exactly that mistake.
        host = next((c for c in chunks if judgement["anchor"] in c.text), None)
        if host is None:
            raise SystemExit(f"{case_id}: anchor not found in any chunk: {judgement['anchor']!r}")
        passage = splice(host.text, judgement["anchor"], judgement["window"])
        page = host.page_number

        record = {
            "case_id": case_id,
            "passage_page": page,
            "category": judgement["category"],
            "human_label": judgement["human_label"],
            "human_justification": judgement["human_justification"],
            "labeller_a": judgement["labeller_a"],
            "labeller_b": judgement["labeller_b"],
            "claim": judgement["claim"],
            "passage": passage,
            "marker_page": page,
        }
        if "human_label_note" in judgement:
            record["human_label_note"] = judgement["human_label_note"]
        for optional in ["marker_source", "marker_source_present", "has_marker"]:
            if optional in judgement:
                record[optional] = judgement[optional]
        lines.append(json.dumps(record, ensure_ascii=False))

    CASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    CASES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {len(lines)} cases to {CASES_PATH.relative_to(PROJECT_ROOT)}")
    print(f"fixture: {len(pages)} pages, {len(chunks)} chunks")
    print(f"source_id: {pages[0].source_id}")

    # Verify immediately: every passage must be a literal substring of the extraction. This is the
    # property that makes the evaluation mean anything, so it is checked here rather than assumed.
    # Both sides are whitespace-normalised because `splice` snaps to word boundaries and the corpus
    # is a join of separately-normalised chunks; the characters themselves must still match.
    flat_passages = [_flatten(json.loads(line)["passage"]) for line in lines]
    flat_chunks = [_flatten(c.text) for c in chunks]
    # A passage may be spliced from any chunk on its page, so membership is tested against the whole
    # corpus. Only the case id and its passage are needed here; pairing positionally with chunks would
    # imply a correspondence that does not exist.
    bad = [
        case_id
        for case_id, passage in zip(JUDGEMENTS, flat_passages)
        if not any(passage in text for text in flat_chunks)
    ]
    total = len(flat_passages)
    print(
        "verbatim check: "
        + (f"all {total} passages found in the extraction" if not bad else f"FAILED {bad}")
    )
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())