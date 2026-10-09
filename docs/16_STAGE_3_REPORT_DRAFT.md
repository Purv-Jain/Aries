# 16 — Stage 3 Report (DRAFT)

**Status:** **DRAFT — not submission-ready.** Two gate items cannot be met while B-05 is open: no
screenshots exist (S1–S9), and no commit authorship exists. See §15.
**Drafted:** 2026-10-08 · **Every number below has a row in
[12_STAGE_3_EVIDENCE_TRACKER.md](12_STAGE_3_EVIDENCE_TRACKER.md) and a captured log in
[logs/](../logs/README.md).**
**Related:** [Evidence Tracker](12_STAGE_3_EVIDENCE_TRACKER.md) · [Deviations §3.1](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log) · [Architecture](04_SYSTEM_ARCHITECTURE.md) · [Evaluation](10_EVALUATION_METRICS.md)

---

## 1. Abstract

Generative AI assistants produce confident, well-formatted academic answers whose citations are
frequently unverifiable. A student cannot distinguish a real source from a plausible-looking
fabricated one without opening and reading every reference. This report describes a fully local
application that answers a question from a user's own academic PDFs, attaches page-level citation
markers to every claim, and then **independently checks whether the cited passage supports the
claim**, labelling each claim `Verified`, `Needs Review`, or `Unsupported` and showing the evidence
beside the score.

The system was built and evaluated against the team's own 15-page, two-column Stage 2 report. On a
24-case hand-labelled set the verifier achieved **precision 1.000, recall 0.800, F1 0.889** for the
`Verified` class, with a **false-`Verified` rate of 0.000** at a calibrated threshold of 0.63 — the
figure the project exists to drive down, and one that moved from 0.125 by measurement rather than
argument. Retrieval reached **Recall@1 0.667** and **Recall@3 1.000** on 9 hand-authored questions.
The offline profile answered in a median of **12.40 ms** (p95 15.55 ms) at **191.3 MB** peak RSS and
returned byte-identical output across five runs, with no network access and no model download.

Two results are reported because they are unflattering. The system originally **did not abstain
out of corpus at all** — a measured 0.000, producing 15 claims labelled `Verified` on questions about
photosynthesis and the northern lights. That failure was found, measured, and then fixed: a gate now
runs before generation and refuses **0.750** of unanswerable questions with **0.000** false
abstentions, though **6 adversarial cases still get confident answers**. And the evaluation set is
**self-authored and self-labelled by the team that wrote the verifier**, so these figures justify an
operating point rather than establish generalisation. Both are stated as limitations in §12 rather
than buried.

## 2. Problem and motivation

Stage 1 documented the problem with a citation: Athaluri et al. reported that ChatGPT invented a
substantial share of its references, complete with plausible-looking but fake DOIs, in medical
research writing. The gap identified was not that AI writes badly — it is that **no lightweight tool
both retrieves the user's own papers and verifies that each claim in the answer actually appears in
the retrieved text**.

Existing tooling addresses the parts separately. RAG frameworks retrieve and generate. Reference
managers check whether a bibliography entry *exists*. Citation checkers verify formatting. During
our evaluation of 18 open-source candidates ([02](02_OPEN_SOURCE_RESEARCH.md)), **every one that
displays citations only formats them; none computes per-claim support against the cited passage.**
That gap is this project's contribution.

The motivation is traceability rather than fluency. A user must be able to open the cited file, go
to the cited page, read the actual passage, and see the score that produced the label. When the system
cannot establish support, it must say so rather than produce a confident sentence.

## 3. Deviations from the Stage 2 report

Stage 2 overrides Stage 1, and Stage 3 overrides neither silently: nine Stage 3 departures from
Stage 2 are recorded in [01 §3.1](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log). The
four that change observable behaviour:

| Deviation | Stage 2 | Stage 3 | Why |
|---|---|---|---|
| **D-11** threshold | 0.62, unmeasured | **0.63**, from a sweep | 0.62 carries a measured false-`Verified` rate of 0.125; 0.63 carries 0.000 |
| **D-13** overlap | unspecified | **containment, not Jaccard** | Claims are short summaries of long passages; Jaccard under-scores correct citations |
| **D-14** contradiction | not described | **numeric, negation-polarity, antonym checks** | High lexical overlap can still mean a contradiction — the case a threshold cannot catch |
| **D-15** injection | not addressed | **detection and flagging** | Retrieved PDF text is untrusted data, never instruction |

Also corrected: Stage 2's quote of "28 chunks from 11 pages" is not repeated anywhere, because it is
inconsistent with its own stated chunk size ([D-17](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log)).

**A finding that did not reproduce.** The Phase 0 audit flagged Stage 2's reference list as
mis-numbered ([I-01](03_GAP_ANALYSIS.md#31-internal-inconsistencies-found-in-the-stage-2-report)).
Checking the extracted text in Phase 7 found `Magesh`, `legal research` and `hallucination-free`
occur **zero** times, and **zero dangling or orphaned references**. The suspicion was wrong. Stage 3
cites only the papers it actually read.

## 4. System architecture

```
PDF upload → validate → page-wise text → sentence-aware chunk → embed → persist
   → retrieve top-k → generate grounded answer with [Sx, p.y] markers
   → verify each claim against its cited evidence
   → label Verified / Needs Review / Unsupported
   → render answer + evidence inspector
```

Two profiles share one pipeline ([ADR-0005](05_TECH_STACK_AND_ADRS.md#adr-0005--two-profiles-one-pipeline)):

| | Semantic profile | Offline profile (**default**) |
|---|---|---|
| Embedding | `all-MiniLM-L6-v2` | TF-IDF |
| Store | Chroma | in-memory, deterministic |
| Generator | optional `flan-t5-small` | extractive |
| Requires | ~90 MB / ~308 MB download | **nothing** |
| Measured? | **no — weights absent** | **yes, every figure in §11** |

Ingestion extracts page-wise with `pypdf`, falling back to `pdfplumber` for near-empty pages.
Chunking uses a regex sentence splitter at 180 words with 30-word overlap and never crosses a page
boundary. Retrieval maps top-k results back to file and page. Full design, including five Mermaid
diagrams and failure modes, is in [04](04_SYSTEM_ARCHITECTURE.md).

## 5. Design decisions

Thirteen ADRs are recorded in [05](05_TECH_STACK_AND_ADRS.md). The four that a reader is most likely
to challenge:

**No LangChain.** It is an orchestration framework; Stage 1 listed it as the language model, which
was factually wrong. Nine direct dependencies are pinned.

**Chunk size 180 words with 30-word overlap.** `all-MiniLM-L6-v2` has `max_seq_length = 256`, read
from the Hugging Face API rather than assumed. Sentences average well under that, so chunks are kept
below the effective input length rather than truncated by it.

**Containment overlap, not Jaccard.** A claim is a short summary of a long passage. Jaccard penalises
exactly the length difference that makes citation valid.

**Verification is a heuristic and is labelled as one.** The label `Verified` means *passed this
project's documented support-check at the configured threshold*. It does not mean the claim is true.
Cosine similarity measures relatedness; it is not entailment and it is not proof. This is enforced in
code: the enum has exactly three values, `Hallucinated` cannot be constructed, and a test rejects
nine forbidden phrasings across four claim shapes.

## 6. Implementation

| Module | Responsibility |
|---|---|
| `src/models.py` | Every dataclass, the reason-code vocabulary, content-derived IDs |
| `src/pdf_ingestion.py` | Validation, extraction, scanned detection, filename sanitisation |
| `src/chunking.py` | Regex sentence splitter, sentence-aware chunking, exact word overlap |
| `src/embeddings.py` | One protocol, two backends; lazy MiniLM with typed degradation |
| `src/vector_store.py` | Deterministic in-memory store and a Chroma adapter |
| `src/generator.py` | Extractive generator (default) and optional FLAN-T5 adapter |
| `src/verifier.py` | **The contribution.** Marker grammar, resolution, support scoring, contradiction checks |
| `src/pipeline.py` | The only orchestrator: `index`, `ask`, `remove_document`, `reindex_document`, `index_stats` |

`app.py` and `run_demo.py` import only `src.pipeline` and `src.models`. This is asserted by an AST
audit, not by convention: neither file may contain a scoring or threshold literal, so the UI cannot
drift from the pipeline's logic.

**Determinism.** Chroma's HNSW is approximate and its tie order arbitrary, so the adapter sets
`hnsw:search_ef = 256`, over-fetches 4× candidates, re-scores with the same similarity function the
in-memory store uses, and breaks ties on `chunk_id`. Both stores return identical top-3 for the same
query. Exactness at large corpus sizes is **not** claimed.

## 7. Open-source research and reuse decisions

Eighteen candidates were evaluated against live GitHub, Hugging Face and PyPI API data, then scored
on a weighted rubric ([02](02_OPEN_SOURCE_RESEARCH.md)). Strategy B — build standalone, reuse
libraries rather than fork — scored **9.00/10** against hybrid 8.00 and the best fork 5.70, because
no candidate satisfied the requirement.

Eight were legally unusable (no licence, `NOASSERTION`, or GPL-3.0 incompatible with distribution).
One (`amazon-science/RefChecker`) is archived. One, `citation-needed/citation-needed`, is a **404** on
GitHub: the real project lives on Wikimedia GitLab, is MIT, dormant, and OpenAI-dependent.

No third-party source is vendored. Both models used are Apache-2.0, verified via the Hugging Face
API.

## 8. Verification design, and its limits

The pipeline is: parse each `[Sx, p.y]` marker; confirm it resolves to a chunk **actually retrieved**
in this query; compute

```
support_score = 0.7 · similarity + 0.3 · token_overlap
```

where `similarity` is TF-IDF cosine or MiniLM cosine depending on profile, and `token_overlap` is
containment. Then apply numeric-mismatch, negation-polarity and antonym checks, and assign the label.

**Retrieval relevance and claim support are different numbers answering different questions.** Chunk
versus query is retrieval; claim versus cited chunk is support. They are never merged, averaged, or
displayed as one figure — a contract test asserts `RetrievalResult` has no `support_score` field at
all, in three separate ways.

**An invalid marker is `Unsupported`.** It is never silently dropped and never guessed at a
plausible target. Silently re-attributing a citation would destroy the one property the project
exists to provide. Measured over the labelled set: fabricated-marker rate **0.000**.

**What this is not.** It is not entailment. A claim and a passage can share every content word and
still differ in scope; a true synonym paraphrase scores ~0.10 containment and is `Unsupported`. The
lexical limit is recorded deliberately rather than papered over by loosening the threshold — a test
fixture guard prevents that.

## 9. User interface

Three surfaces, all reading live pipeline data and nothing else. Warm ivory canvas, deep forest
primary, sage surfaces; serif for prose, monospace for quoted evidence. Every status is
colour **+** icon **+** word, so nothing depends on colour alone.

**13 contrast pairs were measured, 12 at WCAG AA**; the placeholder hint is 3.3:1 against a 3:1
large-text floor and is named as such rather than counted as a pass. The evidence inspector shows
support score and retrieval relevance as **separately labelled rows**.

> **Not yet claimed:** greyscale readability, a keyboard-only walkthrough, and 1280/768 px layout
> have not been checked by a person. The 98 UI tests prove the render path executes and the markup is
> correct; they cannot see a layout. No screenshots are included in this draft.

## 10. Testing

**429 tests, 429 passed, 0 failed, 0 skipped, 0 xfailed.** Captured output:
[logs/02_test_suite_offline.txt](../logs/02_test_suite_offline.txt).

| Suite | Tests | Covers |
|---|---|---|
| `test_core.py` | 64 | ingestion, limits, chunking, ID contracts, security |
| `test_retrieval.py` | 80 | embeddings, stores, retrieval, persistence, degradation |
| `test_verification.py` | 130 | generation, verification, abstention, injection defence |
| `test_ui.py` | 98 | renders, states, inspector, contrast, no-placeholder audit |
| `test_hardening.py` | 57 | evaluation integrity, calibration, **abstention-gate calibration**, security sweep, determinism, metrics, CLI, cross-platform paths, CI config |

All 17 mandated edge cases and all 20 contract tests are covered.

**The six deselected tests have never been run.** They carry the `semantic` marker and require
MiniLM and FLAN-T5 weights, which are absent from this machine. They are written and collectable —
pytest confirming it found them is what "6 deselected" means — but their result is **unmeasured**, and
this report claims nothing about them.

**Offline is proven by construction, not by environment variable.** One test replaces
`socket.connect` and `socket.create_connection` with a function that *raises*, then runs a full
index → ask → verify cycle to completion. The default path is not permitted to try the network.

**Reproducibility.** A second virtual environment built from `requirements.txt` alone passes the same
371 tests (run before the Phase 7 fixes added 34 tests). `pip check` → `No broken requirements found.`

**Continuous integration is green on both platforms.** Run
[37880879892](https://github.com/Purv-Jain/Aries/actions/runs/37880879892) on `66075b`:
`offline (ubuntu-latest)`, `offline (windows-latest)` and `security-sweep` all `success`. Two OSes
because PDF extraction is the layer most likely to differ between them, and a parsing difference that
only appears on one platform is worth finding before a demonstration rather than during one.

Getting there required a genuine cross-platform bug, and the shape of it is worth recording. Three
paths in the hardening tests were built from Windows-style string literals. On POSIX a backslash is
an **ordinary filename character**, so `PROJECT_ROOT / r"tests\data\eval_cases.jsonl"` resolves to a
*single long filename* in the project root rather than a three-part path. Tests that merely checked
`.exists()` would have **skipped silently** and the suite would have reported green on Linux while
part of it never ran; the nine that read the file raised `FileNotFoundError` instead, which is why
the job went red at all. A second instance in `tools/build_cases.py` — the script that regenerates
the evaluation set — was missed by the first fix and is now corrected. `TestPathsAreCrossPlatform`
scans `src/`, `tools/`, `tests/` and the entry scripts for the pattern, so it cannot return.

## 11. Evaluation

All figures from the team's own 15-page Stage 2 report (two-column prose with tables — the hardest
input the project faces). Method for each: [10 §11](10_EVALUATION_METRICS.md#11-results-table--measured-in-phase-6).

### 11.1 Retrieval

| Metric | Value |
|---|---|
| Recall@1 | 0.667 (6/9) |
| Recall@3 / @5 / @10 | 1.000 |
| MRR | 0.778 |
| Marker coverage (extractive) | 1.000 |
| Citation resolution rate | 1.000 |

### 11.2 Verification, on the 24-case labelled set

| Threshold | P(Verified) | R(Verified) | F1 | false-`Verified` |
|---|---|---|---|---|
| 0.30 | 0.643 | 0.900 | 0.750 | 0.357 |
| 0.59 | 0.889 | 0.800 | 0.842 | 0.111 |
| **0.63 — chosen** | **1.000** | **0.800** | **0.889** | **0.000** |
| 0.80 | 1.000 | 0.400 | 0.571 | 0.000 |

0.63 is the highest-F1 point at which no claim is wrongly labelled `Verified`. Sweep output:
[logs/05_evaluate.txt](../logs/05_evaluate.txt).

### 11.3 Performance

| Metric | Value | Method |
|---|---|---|
| Indexing | 3.236 s per 100 pages | 3 runs, median 0.486 s for 15 pages |
| Query p50 / p95 | 12.40 / 15.55 ms | 27 queries after warm-up |
| Peak RSS | 191.3 MB (baseline 190.0 MB) | sampled after each stage, 11 samples |
| Determinism | 1.000 (5/5 runs) | answer + verifications byte-identical |

### 11.4 Explicitly not measured

Model load time · semantic-profile latency and Recall@k · FLAN-T5 marker coverage · semantic
determinism. No model has ever been loaded on this machine, so there is nothing to time. Any figure
here would be invented.

### 11.5 What the evaluation found about itself

**Five real verifier defects.** The first two were invisible to the unit suite and surfaced only by
running the system against real academic text:

1. The negation check compared one sentence against a whole 180-word paragraph. Six plainly-supported
   claims returned `contradiction_detected` because the chunk contained "not an OCR engine" somewhere
   while the claim had no negation.
2. The negation check compared *cue words* rather than *polarity*, so "does not depend" and "no ?
   required" read as opposite.

Accuracy over the 24 cases: **0.292 ? 0.625 ? 0.667** for the first two.

The next three were found later, by writing direct unit tests for helper functions that had only ever
been reached indirectly:

3. **`_antonym_conflict` searched the wrong token set.** It looped over the tokens the claim and the
   passage *shared*. But a contradiction means the claim uses one member of an antonym pair and the
   passage the other, so the token under test is never in that intersection. The function fired only
   when the passage happened to contain *both* members ? the opposite of the disagreement it was
   looking for. **The antonym branch was dead code.**
4. **`_claim_is_negated` could not see most negation cues.** It intersected a token set built by
   `content_tokens`, which drops stopwords ? and `not`, `no`, `nor` and `without` are stopwords. Four
   of the ten cues were invisible, including the commonest one in English. This is precisely the
   mistake the module's own docstring warns against at length.
5. **The antonym list paired inflections individually.** `("increase","decrease")`,
   `("increased","decreased")` and `("increases","decreases")` were three separate pairs, so a claim
   saying "increased" and a passage saying "decreased" never met ? each was paired only with its own
   inflection. Inflections are now grouped by concept, with the seven oppositions declared
   explicitly. Declaring every pair would have been worse: through polysemy it would have made
   `increased` and `cost` antonyms, so "The cost increased" would have been reported as
   self-contradictory. For the same reason the check now **declines** when the passage also uses the
   claim's own direction ? "Accuracy increased while latency decreased" is a mixed result, not a
   denial of the claim.

**Fixing 3, 4 and 5 moved no measured number.** Accuracy stayed at 0.667; precision, recall, F1 and
the false-`Verified` rate are unchanged, and the sweep returns the same threshold of 0.63. All five
defects pushed the same way ? toward *failing* to catch contradictions ? and on this fixture every
contradiction the evaluation credits to the verifier is caught by the numeric and polarity branches.
The calibration was therefore never built on a broken branch.

That is the honest reading, and it carries its own admission: **the antonym branch is correct code
that no measurement in this report exercises.** It is a gap alongside the abstention failure, not a
success. Thirty-one direct tests now cover it, four of which guard the concept list itself as data.

**The evaluation set is self-authored and self-labelled** by the team that wrote the verifier, from a
single 15-page report. 58% of cases are negative or partial, every passage is verbatim-checked against
the extraction, and no case carries an expected system label — but the recorded 0.958 "agreement" is
a self-reconciliation, **not** independent inter-annotator agreement, and is not presented as such.
Recall@1 over 9 questions moves in steps of 0.111. These figures justify an operating point; they do
not establish that the system generalises.

## 12. Limitations and future work

**1. Abstention is lexical, and six adversarial questions still defeat it.** This was the project's
worst measured failure and it was **0.000**: asked about mercury's boiling point, the 2019 Cricket
World Cup and photosynthesis — none in the corpus — the system answered all three, quoting the
least-irrelevant sentence available, at mean support 0.59 across 9 claims. Across 10 out-of-corpus
questions that produced 50 claims, **15 of them labelled `Verified`**. Captured before the fix in the
first commit of `logs/07`–`09`; the current runs show abstention.

The cause was that the generator's only trigger asked "is any sentence relevant enough?" and never
"do these passages answer the question?" — TF-IDF cosine between unrelated English sentences is
near zero but never exactly zero, so something always cleared the bar.

The fix refuses **before** generation, on a threshold calibrated against 48 hand-labelled questions.
The obvious fix was measured and rejected: a floor on the cosine `relevance_score` cannot separate
the two classes (answerable top-1 scores 0.138–0.257, unanswerable 0.072–0.192), so any floor
catching most unanswerable questions also killed at least five of eight answerable ones. The shipped
gate scores **coverage of the question's content words** by the retrieved passages, which does
separate (answerable minimum 0.667, clear unanswerable maximum 0.250), with
`min_query_coverage = 0.50`.

Measured after, on the same corpus:

| Metric | Before | After |
|---|---|---|
| Correct abstention, 24 unanswerable | **0.000** | **0.750** (18/24) |
|  clear negatives | 0.000 | **1.000** (18/18) |
|  adversarial negatives | 0.000 | **0.000** (0/6) |
| False abstention, 24 answerable | 0.000 | **0.000** |
| False-`Verified` claims on the original 10 questions | **15** | **0** |
| Claims emitted on those 10 questions | 50 | **0** |

**The residual failure is not a tuning oversight.** The six misses ask for a fact the report never
states while using vocabulary it does contain — "What is the inference throughput of MiniLM on this
laptop?" names MiniLM and a student laptop, both of which appear. Coverage cannot separate those from
answerable questions, and closing the gap needs entailment rather than a better threshold. They sit
in the labelled set so the headline 0.750 cannot be improved by deleting them.

**2. Verification is lexical support, not entailment.** See §8. A true synonym paraphrase scores
~0.10 and is `Unsupported`. NLI is the documented next step and is out of scope here.

**3. The semantic profile is unmeasured.** No MiniLM or FLAN-T5 weights are present. Its code paths
and their degradation behaviour are tested; its performance is not known.

**4. Single-language, no OCR.** Scanned PDFs produce a clear limitation message rather than an empty
index. English-first, both explicit scope decisions.

**5. The evaluation is small and self-authored.** 24 cases, 9 questions, one document.

**6. The system cannot distinguish a correct claim from a claim that matches an irrelevant passage
well.** This is limitation 1 seen from the other side.

**7. The antonym contradiction branch is unexercised by any measurement.** Three live defects lived
there for six phases ? it searched the wrong token set, its negation guard could not see `not`, and its
inflections never crossed (`increase`/`decrease` and `increased`/`decreased` were separate pairs) ? and
the 24-case set never noticed any of them, because it contains no antonym pair. All three are fixed and
unit-tested, and fixing all three moved accuracy not at all. The branch is correct code that nothing
has been measured against against labelled data (?11.5).

Future work, in the order it would be worth doing: a relevance floor for abstention; a larger
independently labelled set; NLI-based verification; an ablation quantifying what the semantic
profile buys over the offline one.

## 13. Individual contributions

> **A repository now exists, and one of its two commits carries a placeholder author. Both facts are
> stated here rather than smoothed over.**

Commit history as recorded by `git log --pretty=format:"%h %an <%ae> %ad %s" --date=short`:

| Commit | Author | Scope |
|---|---|---|
| `fd2be70` | `Purv-Jain <purv.jain24@sakec.ac.in>` | Phase 7: Stage 3 report draft, reproducible logs, five verifier defects fixed |
| `9772226` | `Your Name <your.email@example.com>` | Phases 0?6: the whole implementation |

`9772226` was authored with the git default placeholder identity ? the repository was created before
the author's name and email were configured. That commit covers **every line of production code and
all but the most recent tests**. It is therefore not usable as evidence of who wrote what.

Two statements follow, and neither is flattering:

1. **`git log --author=` cannot produce this table.** A single commit cannot decompose into three
   contributions. Any per-member figure derived from it would be invented.
2. **Phases 4?6 were largely executed by one AI agent** working from these documents, on the
   direction of the team. Attributing lines to a named student without a commit to prove it is the
   fabrication this report exists to prevent.

What can be stated honestly is **file-level attribution** ? who authored which file in this
workspace ? and even that is partly reconstruction, recorded in
[13_TEAM_CONTRIBUTIONS.md](13_TEAM_CONTRIBUTIONS.md) as such.

### 13.1 What was decided, and why

The option of rewriting `9772226` to attach a correct author was considered and **rejected**. It
changes a commit already pushed to a public repository, invalidates it for anyone who has cloned it,
and requires coordinating two teammates mid-project. A placeholder author on early work is a
documentation defect, not misconduct, and the remedy costs more in trust than the defect does.

The chosen remedy is disclosure: the placeholder is visible in the commit log, stated in this
section, and recorded as **B-05** in the risk register. Fixing it properly is Phase 7 work, after
submission, when rewriting history is cheap because nothing depends on it.

### 13.2 What a reader should conclude

The **implementation** is real, tested and measured ? ?10 and ?11 stand on their own, and every number
in them is reproducible from a command in [logs/](../logs/README.md). What cannot be established from
this repository is **which of the three students wrote which part**. On the evidence available, that
question is open, and the honest position is to say so rather than to produce a table that looks
better than the record supports.

## 14. References

Only sources actually read during this project, each identified so it can be re-read:

[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," NeurIPS 2020.
[2] Y. Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," arXiv:2312.10997, 2023.
[3] S. R. Athaluri et al., "Exploring the Boundaries of Reality: Investigating Artificial Intelligence Hallucination in biomedical research," *Cureus*, 2023.
[4] A. Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection," ICLR, 2024.
[5] UNESCO, *Guidance for Generative AI in Education and Research*, UNESCO Publishing, 2023.
[6] Chroma documentation — open-source retrieval and local persistence, accessed 2026-10-08.
[7] Sentence Transformers `all-MiniLM-L6-v2` model card, Apache-2.0, accessed 2026-10-08.
[8] Streamlit documentation — open-source Python data/AI application framework, accessed 2026-10-08.
[9] `pypdf` CHANGELOG and extraction documentation, accessed 2026-10-08.
[10] Google / Hugging Face `google/flan-t5-small` model card, Apache-2.0, accessed 2026-10-08.
[11] The team's Stage 1 and Stage 2 reports, as the authoritative inputs to this work.

Licence and version verification for each third-party component is recorded in
[02 §3.11](02_OPEN_SOURCE_RESEARCH.md#311-model-licences-verified) and
[README](../README.md#licence-and-attribution).

## 15. What this draft is not yet

Stated plainly so the gap is not mistaken for oversight:

| Missing | Why | Blocked on |
|---|---|---|
| Screenshots S1?S9 | Not captured. None would be fabricated | a human at the screen (7.2) |
| Per-member contribution split | Two commits exist; the Phases 0-6 one carries a placeholder author, so it cannot decompose into three contributions (?13) | **B-05** ? disclosure chosen over rewriting history |
| ~~Green CI run~~ | **ACHIEVED** — run 37880879892 on `66075b`, all three jobs green. Required fixing a Windows-path bug that had the evaluation tests raising `FileNotFoundError` on Linux | — |
| Semantic-profile figures | No model weights on this machine | download + time |
| Greyscale / keyboard / viewport checks | Require a person looking at a screen | Phase 7 manual pass |
| Evaluation cases for the antonym branch | The 24-case set contains no antonym pair, so a corrected branch stays unmeasured | **R-25** — 3-4 cases would close it |
| 6 adversarial abstention misses | Measured, documented, and **left failing on purpose**. A lexical gate cannot separate "the words are here" from "the answer is here" | entailment (P3), not a better threshold |

**Gate G7 is not passed.** See
[15_PROGRESS_TRACKER.md](15_PROGRESS_TRACKER.md#1-current-status).
