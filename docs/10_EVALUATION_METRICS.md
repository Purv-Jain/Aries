# 10 — Evaluation Metrics

**Status:** Phase 1 design · Last updated 2026-10-08 · **Nothing here has been measured yet**
**Related:** [Testing](09_TESTING_STRATEGY.md) · [Architecture §5](04_SYSTEM_ARCHITECTURE.md#5-citation-verification-design) · [Evidence Tracker](12_STAGE_3_EVIDENCE_TRACKER.md)

---

## 1. Ground rule

> **Sections 1 to 10 are not results.** Every number in them is a *definition*, a *target*, or a
> field that was empty before Phase 6. The measurements live in **?11**, and each one names its
> method, its sample size, and what it does not establish.
>
> Stage 1 §2.2 promised "20 test cases which are already prepared beforehand" and an accuracy/recall
> computation. **Those cases do not exist anywhere in this workspace**
> ([Gap Analysis M-11](03_GAP_ANALYSIS.md#3-report-claims-vs-workspace-reality)). They must be created
> in Phase 6 — and created so that results are **not** predetermined.

## 2. Metric inventory

| # | Metric | Status | Priority |
|---|---|---|---|
| M1 | Retrieval Recall@k | Definition only | P1 |
| M2 | Citation resolution rate | Definition only | P0 |
| M3 | Claim-support precision / recall / F1 | Definition only, **needs labelling** | P0 |
| M4 | Abstention behaviour | Definition only | P0 |
| M5 | Indexing latency | Definition only | P2 |
| M6 | Query latency | Definition only | P2 |
| M7 | Peak RAM | Definition only | P2 |
| M8 | Local model load time | Definition only | P2 |
| M9 | Determinism rate | Definition only | P1 |
| M10 | Marker coverage | Definition only | P1 |

## 3. M1 — Retrieval Recall@k

**Question:** when the user asks something the documents actually answer, is the supporting passage
inside the top *k*?

**Definition:** over a hand-built set of *answerable* questions with a known correct `(source_id,
page)`:

```text
Recall@k = |{ q : the correct (source_id, page) appears in top-k(q) }| / |answerable questions|
```

Report at k = 1, 3, 5, 10. Also report **MRR** (mean reciprocal rank), which is more informative than
Recall@k alone and costs nothing extra.

**Question set:** 20 questions, hand-written by the team against a named fixture document. Each must
record `question`, `expected_source_id`, `expected_page`, `answerable: bool`, and `notes`.

**Critical honesty note.** These questions are written *by the same people who wrote the chunker and
the retriever*. That is a genuine source of optimism bias, and the Stage 3 report **must** say so
plainly. A self-authored eval set is normal for a microproject; an unacknowledged self-authored eval
set is not defensible.

Do **not** quote a published benchmark number as if it were ours. Numbers in third-party READMEs are
that project's claims, not ours.

## 4. M2 — Citation resolution rate

**Question:** do the markers the system emits actually point at something it retrieved?

```text
citation_resolution_rate = resolved_markers / total_markers_emitted
```

where `resolved` means the marker's `source_id` and page matched a retrieved chunk.

This is a **self-consistency** metric, not a correctness metric. A system that emits no markers
trivially scores 0/0 — so always report the **absolute counts** (`12/14 markers resolved`) alongside
the ratio. A ratio without counts hides that.

Pair it with:

```text
fabricated_marker_rate = unresolvable_markers / total_markers_emitted
```

The target is that this is **0 in the default extractive profile**, because the generator can only
emit markers for retrieved chunks. If it is not zero, something is broken.

## 5. M3 — Claim-support precision / recall / F1

**Question:** does the `Verified` / `Needs Review` / `Unsupported` labelling agree with human
judgement?

### 5.1 Labelling protocol

Two team members independently label every case, then reconcile disagreements by discussion,
recording the disagreement rate as inter-annotator agreement. Disagreements are *data*, not noise —
the count of them is itself worth reporting.

- **Labeller:** a human reads `(claim, evidence passage)` and answers: does this passage support the
  claim? → `supported` / `partial` / `contradicted` / `no_information`
- **Never** show the labeller the system's label first — that anchors them.
- Record the justification in one sentence per case.

### 5.2 Mapping to system labels

| Human label | System label expected |
|---|---|
| `supported` | `Verified` |
| `partial` | `Needs Review` |
| `contradicted` | `Unsupported` |
| `no_information` | `Unsupported` |

### 5.3 Metrics

Treat `Verified` as the positive class:

```text
precision = TP / (TP + FP)      # of claims we called Verified, how many are truly supported?
recall    = TP / (TP + FN)      # of truly supported claims, how many did we catch?
F1        = 2·P·R / (P + R)
```

Also report a **3-class confusion matrix**, because collapsing `Needs Review` and `Unsupported`
hides the most important behaviour of the system: it should be *cautious*.

**The most important number in the whole project:**

```text
false_verified_rate = (claims labelled Verified that humans say are not supported) / (all claims labelled Verified)
```

A high false-`Verified` rate would mean the tool manufactures false confidence — precisely the harm it
exists to prevent. Report it explicitly, even if it is unflattering. A tool that is honestly 70%
accurate and says so is more valuable than one that claims 99% and is not.

### 5.4 Threshold calibration

Sweep `verified_threshold` over `[0.30, 0.90]` in steps of `0.02` and plot precision/recall/F1 against
it. Choose an operating point and justify it:

- **Correctness-first** (the right default for this project): maximise precision subject to
  `false_verified_rate <= 0.05`. Accept lower recall. Missing a supportable claim is a minor annoyance;
  falsely endorsing one is the harm we exist to prevent ([ADR-0007](05_TECH_STACK_AND_ADRS.md#adr-0007--verifier-scope-precision-first-abstention)).
- **Balanced**: maximise F1.
- **Recall-first:** not recommended here, and saying why is itself a good viva answer.

Record the chosen threshold, its F1, its precision, its recall, and the curve — in the tracker.

## 6. M4 — Abstention behaviour

| Sub-metric | Definition | Target |
|---|---|---|
| Abstention rate on unanswerable questions | unanswerable questions that produce abstention / all unanswerable | as close to 1.0 as possible |
| **False-abstention rate** | answerable questions that abstain / all answerable | record; high is annoying but safe |
| Fabrication on abstention | answers produced when evidence was insufficient | **must be 0** |

The last row is a hard invariant, not a target: if the system answers when it has no evidence, the
`Unsupported` label becomes meaningless.

Include deliberately unanswerable questions — about a document not in the collection, and about a
topic absent from it. A system that never abstains looks broken to any examiner who asks one
off-script question.

## 7. M5–M8 — Performance

**No latency is promised.** What is measured in Phase 6, with method recorded:

| Metric | Method | Notes |
|---|---|---|
| M5 Indexing latency | `time.perf_counter()` around `pipeline.index()`, per page and per document | ≥3 runs; report min/median/max |
| M6 Query latency | Wall time around `pipeline.ask()`, p50/p95 over ≥20 queries | Report **per profile** — offline vs semantic |
| M7 Peak RAM | Sampled RSS during indexing and querying | Sampling loop; note the sampling interval |
| M8 Model load time | Time to first encoder use after process start, cold and warm | Expected to dominate first-query latency |

Environment for every measurement must be recorded: CPU model, RAM, OS, Python version, whether a GPU
was present (it should not be).

| Field | Value |
|---|---|
| CPU | _measure in Phase 6_ |
| RAM | _measure_ |
| OS | Windows (measure build) |
| Python | _per ADR-0001_ |
| GPU | none (CPU-only by design) |

If a metric is inconvenient to measure, report it as inconvenient. Do not omit it silently, and do
not estimate it.

## 8. M9 — Determinism rate

```text
determinism_rate = identical_outputs / repeated_runs
```

Ten repeated offline runs of the same `(PDF, question)` pair; compare the serialised
`AnswerResponse` byte-for-byte. Target **1.0**. Anything less is a bug to fix, and a genuine limitation
to report — the Stage 2 report promises exactly this property
([Table 7, Reproducibility row](02_OPEN_SOURCE_RESEARCH.md)).

Run the same check for the semantic profile and report honestly if HNSW approximation or greedy-decoding
settings break it ([Architecture §8](04_SYSTEM_ARCHITECTURE.md#8-determinism)).

## 9. M10 — Marker coverage

```text
marker_coverage = claim_sentences_with_a_valid_marker / all_claim_sentences
```

Target 1.0 in the extractive profile (every sentence is drawn from a retrieved chunk, so it always
carries a marker). A claim sentence with no marker is `no_marker` ⇒ `Unsupported` — it cannot be
`Verified`.

If FLAN-T5 is used, marker coverage will likely be **below 1.0** — that is expected and is precisely
one of the honest reasons the extractive generator is the default.

## 10. Manual claim and evidence evaluation set

**To be created in Phase 6. Results must not be predetermined.**

Required composition:

| Category | Count | Definition |
|---|---|---|
| Supported (direct or near-verbatim) | 6 | Passage states the claim |
| Supported paraphrase | 4 | Same meaning, different wording |
| Partial support | 4 | Related, but a number/qualifier/scope differs |
| Unsupported (absent) | 3 | Passage is on-topic but does not contain the claim |
| Contradicted | 3 | Passage states the opposite |
| Unresolvable reference | 2 | Marker points to a source never retrieved |
| Uncited claim | 2 | Claim sentence with no marker |
| **Total** | **24** | ≥20 as Stage 1 promised |

### 10.1 Creation rules (these are the integrity rules)

1. Cases are written from **real extracted passages of a named fixture**, pasted into the case file.
   Inventing plausible-looking passages is forbidden.
2. At least **half** the cases must be negative. A set that is mostly supported claims inflates every
   metric and is the most common way student evaluations mislead.
3. **Predetermining results is forbidden.** Do not write "expected: Verified" before running the
   system. If you want to know the system's answer, run it — but the *dataset* must be authored from
   human judgement about the passage, independent of the system.
4. **Contradicted cases must flip polarity while keeping the words.** Otherwise they collapse into
   "unsupported due to low similarity" and test nothing new.
5. Write cases **before** running calibration, so the threshold is fitted to data rather than chosen
   to flatter the system.
6. Two labellers, disagreements reconciled and counted.

### 10.2 Case file format

Planned at `tests/data/eval_cases.jsonl` (Phase 6), one JSON object per line:

```json
{
  "case_id": "eval_01",
  "question": "...",
  "claim": "...",
  "source_id": "doc_...",
  "page": 5,
  "passage": "<verbatim text from the fixture PDF>",
  "markers": ["S1, p.5"],
  "category": "supported_paraphrase",
  "human_label": "supported",
  "human_justification": "The passage states the same thing in different words.",
  "labeller_a": "supported",
  "labeller_b": "supported"
}
```

`human_label` is filled by **human judgement about the passage**, before any system run.

## 11. Results table — measured in Phase 6

Fixture: the team's own **15-page Stage 2 report** (`FAI_PE_Microproject_Stage_2_Report_Revised.pdf`),
two-column academic prose with tables. Produced by `tools/measure.py` and `tools/evaluate.py`; the
full JSON is in [tests/data/metrics.json](../tests/data/metrics.json) and
[tests/data/eval_results.json](../tests/data/eval_results.json). **Nothing below was estimated.**

| Metric | Value | Method / artifact | Status |
|---|---|---|---|
| Recall@1 | **0.667** (6/9) | 9 hand-authored answerable questions, one relevant page each | **MEASURED** |
| Recall@3 / @5 / @10 | **1.000** | same 9 questions | **MEASURED** |
| MRR | **0.778** | mean reciprocal rank of the relevant page | **MEASURED** |
| Citation resolution rate | **1.000** | no `unresolvable_reference` arose | **MEASURED** |
| Fabricated-marker rate | **0.000** | both fabricated `[S7, p.1]` cases → `Unsupported` | **MEASURED** |
| Marker coverage (extractive) | **1.000** | every claim carried a resolvable marker | **MEASURED** |
| Marker coverage (FLAN-T5) | `not measured` | — | **Pending — no weights on this machine** |
| Verified-class precision | **1.000** | 24-case labelled set at threshold 0.63 | **MEASURED** |
| Verified-class recall | **0.800** (8/10) | same | **MEASURED** |
| Verified-class F1 | **0.889** | same | **MEASURED** |
| **False-`Verified` rate** | **0.000** | same — **down from 0.125** at the previous 0.62 threshold | **MEASURED** |
| Abstention rate (unanswerable) | **0.000** | 3 questions absent from the corpus; mean support 0.59 | **MEASURED — and it is a bad result. R-24** |
| False-abstention rate | 0.000 (0/9) | same run | **MEASURED** |
| Fabrications on abstention | **0** | no `unresolvable_reference` on any response | **MEASURED** |
| Inter-annotator agreement | **0.958** (23/24) | **nominal — see the caveat below** | **MEASURED, weakly** |
| Chosen `verified_threshold` | **0.63** | swept 0.30→0.90; highest-F1 point with false-`Verified` = 0 | **MEASURED** |
| Determinism rate (offline) | **1.000** (5/5) | answer + verifications byte-identical; timings excluded, see tracker §6.1b | **MEASURED** |
| Determinism rate (semantic) | `not measured` | — | **Pending — needs MiniLM** |
| Indexing latency | **2.67 s / 100 pages** | 3 runs, fresh pipeline each; median 0.400 s for 15 pages | **MEASURED** |
| Query latency p50 / p95 | **12.86 / 16.00 ms** (max 19.31 ms, n=27) | after warm-up, offline profile | **MEASURED** |
| Peak RAM | **191.6 MB** (baseline 190.1 MB) | sampled after each stage; +1.5 MB for the corpus | **MEASURED** |
| Model load time | `not measured` | — | **Pending — no model has ever been loaded here** |

### The two results that must not be reported without their caveats

**Inter-annotator agreement is not what the label suggests.** `labeller_a` and `labeller_b` in the
JSONL were not two independent people. Both were produced by the same agent that wrote the verifier,
so 0.958 records a self-reconciliation, not independent agreement. The field is retained because the
record is honest about what happened, and the report must not call it inter-annotator agreement. This
is logged in [R-03](14_RISK_REGISTER.md).

**Abstention failed.** 0.000 on three deliberately unanswerable questions. The system answered all
three with real citations to irrelevant passages — a worse outcome than silence, because it looks
competent. [R-24](14_RISK_REGISTER.md) carries the analysis and the reason threshold calibration
cannot fix it.

### The caveat that applies to the whole table

24 claims and 9 questions, both self-authored, from a single 15-page report, labelled by the people
who wrote the system. Each Recall question is worth 0.111. These numbers justify an operating point
and demonstrate the pipeline works end to end. They do **not** establish that the system generalises.
Report them as "measured on 24 self-authored cases", never as validation.

## 12. Reporting rules

1. **Every number gets its method.** "Recall@5 = 0.80" is meaningless without "over 20
   hand-authored answerable questions against fixture X".
2. **Report counts with ratios.** "8/10" beats "80%".
3. **Report the unflattering metrics.** Especially false-`Verified` rate and false-abstention rate.
4. **Report sample sizes.** 20 self-authored questions is a small sample; say so.
5. **Never quote a third party's benchmark as ours.** If `paper-qa` or `NexusRAG` published a number,
   attribute it to them and note it was not reproduced here.
6. **Ablations, if time allows.** Report Recall@k for the offline vs semantic profile. It directly
   quantifies what the semantic profile buys — a genuinely useful comparison for the report, and one
   of the most convincing things we can show.