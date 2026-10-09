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

## 4b. Abstention calibration — the sweep behind `min_query_coverage`

Run on the 48 labelled questions in
[tests/data/abstention_cases.jsonl](../tests/data/abstention_cases.jsonl), scored by
`tools/measure.py` against the real 15-page report. 24 answerable (each naming the page that
answers it) and 24 unanswerable, of which **6 are adversarial**.

**Why the labelled set contains adversarial cases.** The easy negatives — the boiling point of
mercury, the 2019 Cricket World Cup — are out of *domain*, and a gate that detects "wrong domain"
looks far better than one that detects "the answer is not in this corpus". Six cases ask for a fact
the report never states while using vocabulary it does contain:

| Case | Question | Terms present | Coverage |
|---|---|---|---|
| `unans_19` | What is the inference throughput of MiniLM on this laptop? | MiniLM, laptop | 0.750 |
| `unans_20` | How much does the Chroma database cost per month? | Chroma, cost | 0.833 |
| `unans_21` | What recall did retrieval achieve on the Stage 1 report? | retrieval, stage, report | 0.800 |
| `unans_22` | How many evaluation queries were labelled by the two labellers? | evaluation, queries, labelled | 0.500 |
| `unans_23` | What learning rate was used to train the MiniLM embedding model? | MiniLM, embedding, model | 0.714 |
| `unans_24` | Which GPU was used for the reproducible validation run? | validation | 0.800 |

All six are answered by the system. That is the honest ceiling of a lexical gate and it is
reported as such rather than excluded from the denominator.

### The sweep

`floor` is the coverage below which the pipeline refuses. 24 unanswerable and 24 answerable.

| floor | correct abstention | false abstention | TP | FN | FP | TN |
|---|---|---|---|---|---|---|
| 0.05 | 0.375 | 0.000 | 9 | 15 | 0 | 24 |
| 0.25 | 0.583 | 0.000 | 14 | 10 | 0 | 24 |
| 0.30 | 0.667 | 0.000 | 16 | 8 | 0 | 24 |
| 0.40–0.55 | 0.750 | **0.000** | 18 | 6 | 0 | 24 |
| **0.50 (shipped)** | **0.750** | **0.000** | **18** | **6** | **0** | **24** |
| 0.65 | 0.792 | 0.000 | 19 | 5 | 0 | 24 |
| 0.70 | 0.792 | 0.042 | 19 | 5 | 1 | 23 |
| 0.85 | 1.000 | 0.208 | 24 | 0 | 5 | 19 |
| 1.00 | 1.000 | 0.292 | 24 | 0 | 7 | 17 |

### Why 0.50 and not 0.65

**0.65 dominates 0.50 on the table** — higher correct abstention at the same 0.000 false
abstention — and it was still rejected. Its margin to the nearest answerable case is **0.017**:
`ans_19` ("What does the report say about OCR for scanned PDFs?") measures exactly 0.667, so one
re-phrasing of one question, or one chunk-boundary change, would push a legitimate question under
the floor. At 0.50 the margin is **0.167** on the answerable side and **0.250** on the unanswerable
side.

Choosing 0.65 would be fitting the threshold to the dataset that justifies it, which is precisely
what this project's own evidence rules exist to prevent. The mid-gap of the two bounds is 0.458,
and 0.50 is that value rounded to something a person would type.

**Read these as 24 self-authored cases from one 15-page report.** They justify this operating point.
They do not establish it as correct in general — the same caveat that applies to the 34-case
verification set and to [R-10](14_RISK_REGISTER.md).

### What the gate does not do

It is a lexical, pre-generation check on question vocabulary. It does not reason about whether a
passage *entails* an answer, it cannot see a fact that is stated in completely different words, and
it cannot catch the adversarial six. It also deliberately stays shut when a question contains no
content words after stopword removal, because absence of signal is not evidence of absence — see
`src.pipeline.query_coverage`.

## 4c. The antonym branch — the labelled cases R-25 said were missing

R-25 was accurate: the 24-case set contained **no antonym pair at all**, so the contradiction branch
had 31 unit tests and zero labelled evidence. Ten cases were added, authored from real report
passages in `tools/build_cases.py` (every passage verbatim-checked, as the other 24 are).

### Four that must fire

| Case | Page | Claim | Passage says | Pair detected |
|---|---|---|---|---|
| `ant_01` | 5 | “selected instead of a much **smaller** model” | “a much **larger** model” | `smaller/larger` |
| `ant_02` | 14 | “**Larger** chunks reduce silent truncation” | “**Smaller** chunks reduce silent truncation” | `larger/smaller` |
| `ant_03` | 3 | “chunk size was **increased**” | “chunk size has been **reduced**” | `increased/reduced` |
| `ant_04` | 11 | “skipping the markers **degrades** reliability” | “**Improves** reliability for classroom evaluation” | `degrades/improves` |

### Six that must stay silent, each for a different reason

| Case | Why it must not fire |
|---|---|
| `ant_05` | The passage uses the **same** direction (`larger`, `increase`) — a mixed-results clause, not a denial |
| `ant_06` | Restates the passage; `costs` is in both |
| `ant_07` | The claim is **negated** (“was not increased”), which is the same fact as “reduced” |
| `ant_08` | **Different subject.** “The number of retrieved passages increased” vs a passage whose “reduces” belongs to “overlap reduces the chance of a chunk-boundary split” |
| `ant_09` | **Different subject, no shared vocabulary at all.** “The paid API expenditure increased” vs a 300-char window about reproducibility and blind trust |
| `ant_10` | The claim carries a direction (`improved`) but the passage contains **no opposite** of it |

### The fourth defect these cases found

`ant_08` and `ant_09` were **reported as `contradiction_detected` before the subject gate existed.**
A claim about any subject at all was contradicted as long as the passage contained an opposite
direction word *somewhere* in it. `ant_09` in particular told the user the source said the opposite
of a claim about paid API expenditure, when the source was a table row about reducing blind trust.

That is worse than a missed contradiction, because it is a confident and wrong explanation. The gate
now requires the claim to be about the **sentence carrying the antonym**, with one exemption: a
single-sentence passage, because there is nowhere else the claim could be about. Without that
exemption, “It was profitable.” against “It was expensive.” would stop being detected.

Measured: **4/4 fire, 6/6 silent, 34/34 cases match their human label on reason.** A test asserts the
gate's result set is a *subset* of the unguarded one across 100+ word pairs, so it can never invent a
detection.

### Effect on the calibration

| Metric | 24 cases | 34 cases |
|---|---|---|
| Accuracy | 0.667 | **0.735** |
| `Verified` precision | 1.000 | **1.000** |
| `Verified` recall | 0.800 | **0.846** |
| `Verified` F1 | 0.889 | **0.917** |
| False-`Verified` | 0.000 | **0.000** |
| Chosen threshold | 0.63 | **0.63** |

The operating point did not move. Ten more labelled cases, seven of them new positives, changed the
scores and left the threshold alone — which is the outcome a calibration wants, and not a guarantee
that 0.63 is right. All 24 pre-existing cases produce byte-identical results before and after.

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

**Two kinds, and the second is the one that matters.** Out-of-*domain* questions (mercury, cricket)
are easy for any lexical check. Questions whose vocabulary overlaps the corpus while the answer does
not exist (MiniLM throughput, Chroma pricing) are the real test, and they are the six
`unans_19`–`unans_24` rows in [4b](#4b-abstention-calibration--the-sweep-behind-min_query_coverage).
An abstention rate measured only on out-of-domain questions describes a system that detects
*subject matter*, not a system that detects *absence of evidence*, and those are not the same claim.

**Implementation note.** `tools/evaluate.py` scores the *verifier* directly against each case's own
cited passage and never calls `pipeline.ask()`, so the abstention gate is **not** in its path. The
gate is measured by `tools/measure.py` and locked by `TestAbstentionGateIsCalibrated` in
`tests/test_hardening.py`. The 34-case verification set and the 48-case abstention set measure
different components and are not substitutes for each other.

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
| Verified-class precision | **1.000** | 34-case labelled set at threshold 0.63 | **MEASURED** |
| Verified-class recall | **0.846** (11/13) | same — up from 0.800 when 10 antonym cases were added | **MEASURED** |
| Verified-class F1 | **0.917** | same — up from 0.889 | **MEASURED** |
| **False-`Verified` rate** | **0.000** | same — **down from 0.125** at the previous 0.62 threshold | **MEASURED** |
| **Correct abstention rate** (unanswerable) | **0.750** (18/24) | 48-case labelled set, `tests/data/abstention_cases.jsonl` | **MEASURED** — up from **0.000**. See [R-24](14_RISK_REGISTER.md) |
|  └─ clear negatives | **1.000** (18/18) | same | **MEASURED** |
|  └─ adversarial negatives | **0.000** (0/6) | same | **MEASURED — the gate's limit, not a defect to hide** |
| **False-abstention rate** (answerable) | **0.000** (0/24) | same | **MEASURED** — up from 0/9 questions; the set grew |
| Unsupported answer rate on unanswerable | 0.250 (6/24) | same | **MEASURED** — the adversarial six |
| False-`Verified` claims on clear out-of-corpus questions | **0** | the 10 questions from the original failure, gate on vs off | **MEASURED** — was **15** |
| `min_query_coverage` floor | **0.50** | swept 0.00→1.00 on the labelled set; see § below | **MEASURED** |
| Fabrications on abstention | **0** | no `unresolvable_reference` on any response | **MEASURED** |
| Inter-annotator agreement | **0.958** (23/24) | **nominal — see the caveat below** | **MEASURED, weakly** |
| Chosen `verified_threshold` | **0.63** | swept 0.30→0.90; highest-F1 point with false-`Verified` = 0 | **MEASURED** |
| Determinism rate (offline) | **1.000** (5/5) | answer + verifications byte-identical; timings excluded, see tracker §6.1b | **MEASURED** |
| Determinism rate (semantic) | `not measured` | — | **Pending — needs MiniLM** |
| Indexing latency | **3.236 s / 100 pages** | 3 runs, fresh pipeline each; median 0.486 s for 15 pages | **MEASURED** |
| Query latency p50 / p95 | **12.40 / 15.55 ms** (max 16.35 ms, n=27) | after warm-up, offline profile | **MEASURED** |
| Peak RAM | **191.3 MB** (baseline 190.0 MB) | sampled after each stage; +1.3 MB for the corpus | **MEASURED** |
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
