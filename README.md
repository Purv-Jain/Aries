# RAG-Based Academic Research Assistant with Citation Verification

**Status:** Phase 6 complete — built, tested, calibrated and measured on a real 15-page paper.
**Current gate:** `AWAITING PHASE 7 APPROVAL`
**Tests:** `pytest -q` → **371 passed, 6 deselected**, 0 failures (2026-10-08)
**Run it:** `streamlit run app.py`
**Last updated:** 2026-10-08

---

## What this project is

A fully local, zero-paid-API application that ingests academic PDFs, answers a question using only
text retrieved from those PDFs, attaches page-level citation markers to every claim, and then
**checks whether each claim is actually supported by the passage it cites**.

The distinguishing feature is not answer fluency. It is **traceability**: a student must be able to
open the cited file, go to the cited page, read the actual passage, and see the support score that
produced the label.

## Team

| Member | PRN | Primary Stage 3 ownership |
|---|---|---|
| Rishabh Jain | 124BTCM1054 | Citation verification module, threshold calibration, architecture review |
| Purv Jain | 124BTCM1171 | Pipeline integration, retrieval, Streamlit UI |
| Bhavya Soni | 124BTCM1215 | PDF ingestion, test suite, documentation, evidence tracker |

Project guide: Prof. Priyanka Kharatmol

## Authoritative inputs

Stage 2 overrides Stage 1 wherever they conflict. See
[docs/01_REQUIREMENTS.md](docs/01_REQUIREMENTS.md#3-stage-2-versus-stage-1-deviations-log) for the full
deviations log.

| Document | Location |
|---|---|
| Stage 1 report | `docs/reference/stage1_report_text.md` (extracted from the submitted PDF) |
| Stage 2 report (revised) | `docs/reference/stage2_report_text.md` (extracted from the submitted PDF) |

> The original PDFs are not inside this repository. Ask the team for them if the extracted text is
> ever in doubt — the extraction is a convenience, the PDFs remain the source of truth.

## Tech stack (fixed)

Python **3.14.6** (pinned, ADR-0001) · `pypdf` + `pdfplumber` · `sentence-transformers/all-MiniLM-L6-v2` ·
`chromadb` · `scikit-learn` · optional `google/flan-t5-small` · Streamlit · `pytest` · Git/GitHub.

No LangChain. No paid APIs. No GPU requirement. Rationale in
[docs/05_TECH_STACK_AND_ADRS.md](docs/05_TECH_STACK_AND_ADRS.md).

## What exists right now

| Path | What it does | State |
|---|---|---|
| `src/models.py` | Every shared dataclass, the reason-code vocabulary, the content-derived ID scheme | implemented, tested |
| `src/pdf_ingestion.py` | Validation, `pypdf` extraction with a `pdfplumber` fallback, scanned detection, filename sanitisation, injection-pattern flagging | implemented, tested |
| `src/chunking.py` | Regex sentence splitter, sentence-aware chunking with an exact word overlap, no cross-page chunks | implemented, tested |
| `src/embeddings.py` | One protocol, two backends: TF-IDF (default, no download) and lazy MiniLM that fails in a way the pipeline can degrade from | implemented, tested |
| `src/vector_store.py` | Deterministic in-memory store plus a Chroma adapter; `top_k` clamped in one place, ties broken on `chunk_id` | implemented, tested |
| `src/pipeline.py` | The only orchestrator: `index`, `remove_document`, `reindex_document`, `index_stats`, `_retrieve` | implemented, tested |
| `src/generator.py` | Extractive grounded generator (default, offline, injection-proof) plus an optional FLAN-T5 adapter that degrades visibly | implemented, tested |
| `src/verifier.py` | **The project's contribution.** Marker grammar, resolution, containment overlap, `0.7·sim + 0.3·overlap`, numeric and contradiction checks, config-driven labels | implemented, tested |
| `tests/test_core.py` | 64 tests — ingestion, limits, chunking, ID contracts, security | implemented, all passing |
| `tests/test_retrieval.py` | 80 tests — embeddings, stores, retrieval, persistence, degradation | implemented, all passing |
| `tests/test_verification.py` | 83 tests — generation, verification, abstention, injection defence | implemented, all passing |
| `tests/test_ui.py` | 98 tests — renders, states, inspector, contrast, no-placeholder audit | implemented, all passing |
| `tests/test_hardening.py` | 46 tests — evaluation integrity, calibration re-run, security sweep, determinism, metrics, CLI, CI config | implemented, all passing |
| `tests/conftest.py` | The in-process PDF builder and every document fixture | implemented |
| `pytest.ini` | Registers the `semantic` marker; the default run is offline-only | implemented |
| `app.py` | The whole UI: dashboard, document library, research workspace, evidence inspector, verification panel. Imports only the pipeline — never a leaf module | implemented, tested |
| `requirements.txt` | 9 pinned direct dependencies | verified by a clean install |
| `run_demo.py` | CLI reproducible run: index → ask → verify, exit 0/1/2, `--json` | implemented, tested |
| `tools/evaluate.py`, `tools/build_cases.py` | 24-case labelled set from the real report; threshold sweep | measured |
| `tools/measure.py` | Latency, Recall@k, MRR, RAM, determinism, abstention | measured |
| `tests/data/eval_cases.jsonl` | The 24 hand-labelled cases; every passage verbatim-checked | measured |
| `tests/data/metrics.json`, `eval_results.json` | Raw measurement output — the source of every reported number | measured |
| `.github/workflows/tests.yml` | Offline CI on Python 3.14 | **written, never executed** — no repository (B-08) |

## What the system does today

```
PDF → page-wise text → 180/30-word chunks → TF-IDF → top-k
    → extractive answer with [Sx, p.y] markers
    → per-claim support score → Verified / Needs Review / Unsupported
```

Eight claims scored against one retrieved passage, so the labels are demonstrably doing work:

| Claim | Label | Support | Reason |
|---|---|---|---|
| verbatim copy | Verified | 1.000 | `supported` |
| near paraphrase | Verified | 0.632 | `supported` |
| correct words, wrong page | Unsupported | 0.000 | `page_mismatch` |
| negation flipped | Needs Review | 0.000 | `contradiction_detected` |
| wrong year | Unsupported | 0.000 | `numeric_mismatch` |
| unrelated topic | Unsupported | 0.000 | `no_support` |
| fabricated `[S7, p.1]` | Unsupported | 0.000 | `unresolvable_reference` |
| partially wrong ("but requires a database server") | Needs Review | 0.000 | `contradiction_detected` |

`Verified` means *passed this project's documented support-check heuristic at the configured
threshold* — lexical and semantic correspondence, **not** logical entailment and **not** proof that
the claim is true.

The threshold is now a measurement rather than a guess. Sweeping `verified_threshold` over a
24-case labelled set built from the team's own 15-page Stage 2 report:

| Threshold | Verified precision | Verified recall | F1 | false-`Verified` |
|---|---|---|---|---|
| 0.30 | 0.643 | 0.900 | 0.750 | 0.357 |
| 0.59 | 0.889 | 0.800 | 0.842 | 0.111 |
| **0.63 — chosen** | **1.000** | **0.800** | **0.889** | **0.000** |
| 0.80 | 1.000 | 0.400 | 0.571 | 0.000 |

0.63 is the highest-F1 point at which **no** claim is wrongly labelled `Verified`. The previous value
of 0.62 was inherited from Stage 2 and carried a measured false-`Verified` rate of 0.125.

### What the measurements say, including the unflattering parts

Measured on the real 15-page report: Recall@1 **0.667**, Recall@3/5/10 **1.000**, MRR **0.778**,
indexing **2.67 s per 100 pages**, query p50/p95 **12.86/16.00 ms**, peak RAM **191.6 MB**,
determinism **5/5** byte-identical runs.

**The abstention test failed.** Asked about mercury's boiling point, the 2019 Cricket World Cup and
photosynthesis — none of them in the corpus — the offline profile answered all three, citing the
least-irrelevant sentence it could find, at mean support 0.59. The abstention path itself is
correct; the generator's trigger is not. Tracked as **R-24**, and it is reported here rather than
buried because a system that cites irrelevant passages confidently is the exact failure this project
claims to detect.

Full results, with method and caveat for each: [docs/10 §11](docs/10_EVALUATION_METRICS.md#11-results-table--measured-in-phase-6)
and [docs/12 §9](docs/12_STAGE_3_EVIDENCE_TRACKER.md#9-metric-evidence).

## Documentation map

Read these in order if you are new.

| Doc | Purpose |
|---|---|
| [00_PROJECT_CHARTER.md](docs/00_PROJECT_CHARTER.md) | Scope, constraints, success criteria, deadline |
| [01_REQUIREMENTS.md](docs/01_REQUIREMENTS.md) | Functional/non-functional requirements, acceptance criteria, deviations log |
| [02_OPEN_SOURCE_RESEARCH.md](docs/02_OPEN_SOURCE_RESEARCH.md) | 18 evaluated candidates with live evidence, weighted scoring, adoption decision |
| [03_GAP_ANALYSIS.md](docs/03_GAP_ANALYSIS.md) | What the reports claim vs. what actually exists in this workspace |
| [04_SYSTEM_ARCHITECTURE.md](docs/04_SYSTEM_ARCHITECTURE.md) | Pipeline design, data flow, Mermaid diagrams, failure modes |
| [05_TECH_STACK_AND_ADRS.md](docs/05_TECH_STACK_AND_ADRS.md) | Technology decisions and rejected alternatives |
| [06_IMPLEMENTATION_ROADMAP.md](docs/06_IMPLEMENTATION_ROADMAP.md) | Dependency-ordered phases, timeboxes, exit gates, ownership |
| [07_UI_UX_DESIGN_SPEC.md](docs/07_UI_UX_DESIGN_SPEC.md) | Design system, layout, states, accessibility, Streamlit method |
| [08_DATA_MODELS_AND_API_CONTRACTS.md](docs/08_DATA_MODELS_AND_API_CONTRACTS.md) | Typed structures and pipeline contracts |
| [09_TESTING_STRATEGY.md](docs/09_TESTING_STRATEGY.md) | All mandated test scenarios, fixtures, CI |
| [10_EVALUATION_METRICS.md](docs/10_EVALUATION_METRICS.md) | Metric definitions, the 24-case labelling plan, and **the measured results** |
| [11_DEMO_AND_VIVA_PREPARATION.md](docs/11_DEMO_AND_VIVA_PREPARATION.md) | Demo script, likely examiner questions, traps |
| [12_STAGE_3_EVIDENCE_TRACKER.md](docs/12_STAGE_3_EVIDENCE_TRACKER.md) | Every future report claim → the artifact that must back it |
| [13_TEAM_CONTRIBUTIONS.md](docs/13_TEAM_CONTRIBUTIONS.md) | Planned ownership vs. verified actual contributions |
| [14_RISK_REGISTER.md](docs/14_RISK_REGISTER.md) | Live risk register with owners and mitigations |
| [15_PROGRESS_TRACKER.md](docs/15_PROGRESS_TRACKER.md) | Phase status, blockers, next action |
| [AGENTS.md](AGENTS.md) | **Mandatory reading** for any AI agent working in this repo |

## The interface

Three surfaces, all reading live data from the pipeline and nothing else:

- **Dashboard** — live document/page/chunk counts, the upload zone stating its own limits and the OCR
  exclusion *before* you upload, and every file that failed indexing with the real reason and what to
  do about it.
- **Document library** — real rows with pages, chunks and engine; remove confirms first; reindex says
  plainly when the original file is no longer in the session.
- **Research workspace** — the question, the answer with `[Sx, p.y]` markers, the verification panel
  with counts and the weakest score (never an average), and the evidence inspector showing the actual
  passage, the support score and the retrieval relevance as **separately-labelled rows**.

Design: warm ivory canvas, deep forest primary, sage surfaces; serif for prose, mono for quoted
evidence. 13 contrast pairs measured, 12 at WCAG AA. Every status is colour **+** icon **+** word, so
nothing depends on colour alone. Full spec in
[docs/07_UI_UX_DESIGN_SPEC.md](docs/07_UI_UX_DESIGN_SPEC.md).

## Ground rules

1. **Never fabricate.** No invented test counts, commit hashes, metrics, screenshots, or
   verification rates. Every number in the Stage 3 report must exist in
   [12_STAGE_3_EVIDENCE_TRACKER.md](docs/12_STAGE_3_EVIDENCE_TRACKER.md) with a source.
2. **Cosine similarity is not proof.** `Verified` means "passed our documented support-check
   heuristic", never "proven true". This wording must survive into the report.
3. **Citations must resolve.** A marker that does not point to a retrieved chunk is `Unsupported`,
   never silently dropped.
4. **Retrieval score ≠ support score.** They answer different questions and must stay visually and
   numerically separate.
5. **The deterministic fallback must always work.** Same PDF + same question ⇒ same output, with no
   network and no model download.
6. **Phase gates are real.** Do not start Phase N+1 work without an explicit
   `APPROVE PHASE N` instruction.
7. **"Measured" is not "written".** The semantic-profile tests exist and are deselected by default;
   they have never been run because the weights are absent. They are not passing.
8. **CI is not running.** `.github/workflows/tests.yml` exists and has never executed — this
   directory is not a git repository. Nothing here may be called "CI-verified".
9. **Report the bad results.** Abstention measured 0.000 (R-24). It is in this README and in the
   evidence tracker for the same reason the good numbers are: a report that shows only favourable
   measurements is not measurable, it is marketing.

## Quick reference

```bash
python -m venv .venv
.venv\Scripts\activate                      # Windows
pip install -r requirements.txt             # verified working on CPython 3.14.6
pytest -q                                   # 371 passed, 6 deselected as of 2026-10-08
pytest -q -m semantic                       # needs MiniLM + FLAN-T5 weights; never run yet
streamlit run app.py                        # the application
python run_demo.py --pdf <path>             # CLI: index -> ask -> verify, exit 0/1/2
python tools/evaluate.py                    # score the labelled set, sweep the threshold
python tools/measure.py --pdf <path>        # latency, Recall@k, RAM, determinism, abstention
```

`tools/evaluate.py` and `tools/measure.py` expect the Stage 2 report at
`~/Downloads/.pdf/FAI_PE_Microproject_Stage_2_Report_Revised.pdf`, which is **outside this
repository** (B-07). Without it they skip rather than fail.

Use the pinned interpreter. `C:\Python314\python.exe` happens to have most of the stack, but the
**verified** environment is `.venv`, and that is where all 371 passing tests were observed.

## Licence and attribution

This repository is the team's own work. It consumes, but does not vendor, third-party components;
each keeps its own licence:

| Component | Licence | Note |
|---|---|---|
| `pypdf` | BSD-3-Clause | Verified via PyPI metadata, 2026-10-08 |
| `pdfplumber` | MIT | Verified via PyPI metadata, 2026-10-08 |
| `scikit-learn` | BSD-3-Clause | Verified via PyPI metadata, 2026-10-08 |
| `chromadb` | Apache-2.0 | See ADR-0004 for the licence caveat |
| `sentence-transformers` | Apache-2.0 | Verified via PyPI metadata, 2026-10-08 |
| `streamlit` | Apache-2.0 | Verified via PyPI metadata, 2026-10-08 |
| `sentence-transformers/all-MiniLM-L6-v2` | Apache-2.0 | Verified via HF API, 2026-10-08 |
| `google/flan-t5-small` | Apache-2.0 | Verified via HF API, 2026-10-08 |

No third-party source code is copied into this repository. Research findings and the reasoning for
not reusing specific projects are recorded in
[docs/02_OPEN_SOURCE_RESEARCH.md](docs/02_OPEN_SOURCE_RESEARCH.md).