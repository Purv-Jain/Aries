# 03 — Gap Analysis

**Status:** Phase 1 baseline · Audited 2026-10-08
**Related:** [Requirements](01_REQUIREMENTS.md) · [Open-Source Research](02_OPEN_SOURCE_RESEARCH.md) · [Progress Tracker](15_PROGRESS_TRACKER.md) · [Evidence Tracker](12_STAGE_3_EVIDENCE_TRACKER.md)

---

## 1. Headline finding

> **The Stage 2 prototype code does not exist in this workspace.**
>
> Stage 2 §2.3 and §7.1 describe a working local prototype: 11 pages extracted, 28 chunks produced,
> 10/10 automated tests passing, four specific commit hashes. Those statements are **report
> evidence about a prior local integration prototype, not about any code present here.** A full
> search of the workspace found no `src/pdf_ingestion.py`, no `src/verifier.py`, no
> `src/chunking.py`, no `run_demo.py`, and no `app.py` belonging to this project.
>
> **Consequence:** every Stage 2 capability must be treated as `Planned` again. Nothing may be
> reported as `Implemented`, `Verified` or `Measured` until it is re-built and re-measured here.

## 2. Workspace audit

### 2.1 What was searched

| Search | Scope | Result |
|---|---|---|
| Home directory listing | `C:\Users\purvj` | No project folder matching this microproject |
| `Desktop`, `Documents`, `Downloads`, `OneDrive\*` | Recursive | Only unrelated content |
| Filename search for `pdf_ingestion.py`, `chunking.py`, `verifier.py`, `vector_store.py`, `run_demo.py` | Depth 6 across the profile | One hit only: `Resume_Matching\backend\src\embeddings\vector_store.py` — **unrelated project** |
| `requirements.txt` search | Depth 5 | Two hits, both in `Resume_Matching` |
| Git repository check | `C:\Users\purvj` | **Not a git repository** |
| This project directory | Created 2026-10-08 | Previously did not exist |

### 2.2 Reference documents — located

Both authoritative PDFs were found, but **not** at the filenames given in the brief and **not**
inside this project:

| Requested name | Found path | Size |
|---|---|---|
| `FAI&PE_Microproject_stage_1_report(2).pdf` | `C:\Users\purvj\Downloads\.pdf\FAI&PE_Microproject_stage_1_report.pdf` | 434,870 bytes |
| `FAI_PE_Microproject_Stage_2_Report_Revised(3).pdf` | `C:\Users\purvj\Downloads\.pdf\FAI_PE_Microproject_Stage_2_Report_Revised.pdf` | 764,646 bytes |

Nearby duplicates also exist and were **not** used: `FAI_PE_Microproject_Stage_2_Report.pdf`,
`FAI_PE_Microproject_Stage_2_Similarity.pdf`, and `.docx`/`.txt` variants of both reports.

Text was extracted from the two PDFs above with `pdfplumber` into
[`docs/reference/`](reference/) for durable, greppable access:

| Extracted file | Pages | Extracted text | Markdown size |
|---|---|---|---|
| [`reference/stage1_report_text.md`](reference/stage1_report_text.md) | 11 | 21,862 bytes | 22,796 bytes |
| [`reference/stage2_report_text.md`](reference/stage2_report_text.md) | 15 | 32,679 bytes | 33,654 bytes |

**Caveat:** the extraction is a convenience. The submitted PDFs remain the source of truth. The
extracted text preserves page markers but loses figures (Stage 2 Figures 1–5 are images), so any
claim about a *figure's* content must be checked against the PDF.

### 2.3 Environment audit (measured, not assumed)

| Item | Value | Source |
|---|---|---|
| Python | **3.14.6** at `C:\Python314\python.exe` | `python --version` |
| `pip` list | `streamlit 1.65.0`, `sentence-transformers 5.7.0`, `transformers 5.14.1`, `torch 2.13.0`, `scikit-learn 1.9.0`, `numpy 2.4.6`, `pandas 3.0.5`, `pypdf 6.19.0`, `pdfplumber 0.11.10`, `pytest 9.1.1` | `pip list` |
| **`chromadb`** | **NOT INSTALLED** | `pip list` |
| Git | 2.55.0.windows.3 | `git --version` |
| Node | v24.18.0 (not needed) | `node --version` |
| OS | Windows, PowerShell 5.1 | Shell |
| Network | Available (GitHub API, HF API, PyPI all reachable) | Live fetches succeeded |
| Global git identity | Present (`C:\Users\purvj\.gitconfig`) | Not inspected in detail |

**Most of the Stage 2 stack is already installed globally**, which is a genuine time saver. The
exception is `chromadb` — see [R-01](14_RISK_REGISTER.md).

### 2.4 Unrelated project present — do not touch

`C:\Users\purvj\OneDrive\Desktop\Resume_Matching` is a separate FastAPI + Next.js + Qdrant project with
its own `.git`, `venv`, and `AGENTS.md`. It is **not** part of this microproject. It appears in this
audit only because a filename search for `vector_store.py` matched it. Do not modify, reuse, or
reference it.

## 3. Report claims vs. workspace reality

| # | Stage 2 claim (location) | Workspace reality | Classification | Action |
|---|---|---|---|---|
| G-01 | "A modular Python project structure has been defined and exercised with a reproducible local demo" (§1.2) | No project code exists | **Historical report claim only** | Rebuild |
| G-02 | "extracted all 11 pages, produced 28 evidence chunks" (§1.1) | Not reproducible here | **Historical** | Re-measure; do not reuse "28" |
| G-03 | "passed 10 automated tests" (§1.1, §1.2, §7.1) | No tests exist | **Historical** | Re-author and re-run; never state 10/10 for the new codebase |
| G-04 | "TC-02 Extract Level 1 report PDF → 11 pages extracted" (Table 10) | Not reproducible | **Historical** | Re-run; note the report itself says "the Level 1 report", while the query in the text says "Table 1 resource selection" — see [G-13](#31-internal-inconsistencies-found-in-the-stage-2-report) |
| G-05 | Commit `df05016` "feat: add PDF ingestion and chunking foundation" (Table 6) | Not in this workspace; no git repo | **Historical, unattributable** | Do not reuse these hashes. Stage 2 itself warns they "must not be presented as evidence of an individual's work" |
| G-06 | Commits `a6bb764`, `5acd899`, `8b85be0` (Table 6) | Same | **Historical, unattributable** | Same as G-05 |
| G-07 | "The run used Python 3.13.5" (§2.3) | Machine has **3.14.6** only | **Historical + environment drift** | Pin a version deliberately — [ADR-0001](05_TECH_STACK_AND_ADRS.md#adr-0001--pin-the-python-version) |
| G-08 | "Figure 4 is an interface preview rather than a fabricated production screenshot" (§2.3) | Honest disclosure by the team | **Valid, and a good precedent** | Repeat this discipline in Stage 3: label every screenshot as captured or schematic |
| G-09 | Stage 2 says thresholds are "configuration values, not universal constants" (§2.1.5) | No config object exists | **Design intent, unimplemented** | Implement `VerificationConfig` in Phase 4 |
| G-10 | Stage 2 says "report precision/recall later" (Table 7) | No labelled dataset exists | **Not started** | Build the 20-case set in Phase 6 — [10_EVALUATION_METRICS.md](10_EVALUATION_METRICS.md) |
| G-11 | Stage 1 §2.2: "20 test cases which are already prepared beforehand" | **No such cases found anywhere** | **Missing input** | Must be created from scratch in Phase 6 |
| G-12 | Stage 1 §5.2: comparison of MiniLM vs `BAAI/bge-small-en-v1.5` | No results file exists | **Missing evidence** | Either redo honestly in Phase 6 or omit the claim |
| G-13 | Stage 2 §2.1.2 says chunking is "preserves the source filename and page number" — correct, but §2.1.1 never states the **stable source ID** scheme | Undefined | **Design gap** | Specify ID derivation in [08_DATA_MODELS_AND_API_CONTRACTS.md](08_DATA_MODELS_AND_API_CONTRACTS.md) |
| G-14 | Stage 2 §7.1 TC-05 expects "ChromaDB chunk ranked first" using an **offline** profile | Contradiction: Chroma is a semantic-profile component; the validation profile is meant to be Chroma-free | **Test-design inconsistency** | Rewrite TC-05 to name the store actually used |
| G-15 | Stage 2 §1.1 says the validation run used "the Level 1 report itself as a reproducible input document", but the team has `FAI_PE_Microproject_Stage_2_Report_Revised.pdf` as the natural fixture | Ambiguous | **Fixture clarity** | Standardise the fixture set in Phase 2 — [09_TESTING_STRATEGY.md](09_TESTING_STRATEGY.md) |

### 3.1 Internal inconsistencies found in the Stage 2 report

These are **not** fatal, but Stage 3 should not silently inherit them:

| # | Finding | Location | Impact |
|---|---|---|---|
| ~~I-01~~ | Reference list dropped Magesh et al. (Stage 1 `[4]`), so Stage 2's `[4]` was suspected of pointing at Asai/Self-RAG while the prose still discussed "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools" | Stage 2 §2.1.5 vs. reference list `[4]` | **Checked in Phase 7 against the extracted text; the suspicion was wrong.** "Magesh", "legal research" and "hallucination-free" occur **0 times** in the Stage 2 report. Stage 2 dropped the Magesh citation *and* its prose together, and its single `[4]` now correctly supports the Self-RAG sentence. A citation audit also found **0 dangling and 0 orphaned references** in Stage 2. Stage 3 still cites only what it read ([D-19](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log)) rather than renumbering a list it did not write |
| I-02 | Stage 2 §2.1.2 says chunking "is sentence-aware and preserves the source filename and page number" but the Stage 2 module table (`Table 2`) shows no explicit sentence-splitting dependency | Stage 2 §2.1.2, Table 2 | Implementation detail was never pinned down. Specify regex-based sentence splitting in [ADR-0003](05_TECH_STACK_AND_ADRS.md#adr-0003--sentence-splitting-without-an-nlp-dependency). |
| I-03 | Chunking described in §1.1 as "sentence-aware overlapping" but no sentence-boundary algorithm named | Stage 2 §1.1 | Same as I-02 |
| I-04 | TC-05 expects a ChromaDB ranking inside the offline validation profile | Stage 2 Table 10 | See G-14 |
| I-05 | Stage 2 §2.3 claims 28 chunks from 11 pages ≈ 2.5 chunks/page ≈ 70 words/chunk — inconsistent with the stated ~180 words/chunk default for an 11-page report | Stage 2 §1.1 vs §2.1.2 | The 28 figure probably came from a different chunk size. Do not reuse "28 chunks" as an expected value. |

I-05 is worth dwelling on: it is exactly the kind of internal inconsistency an examiner can find with
a calculator. Stage 3 must report **our own measured** chunk count for a named fixture, never inherit
a number whose derivation we cannot reproduce.

### 3.2 Requirements Stage 2 never covered

| # | Missing requirement | Why it matters | Added as |
|---|---|---|---|
| M-01 | Prompt-injection defence for PDF content | Retrieved text is attacker-controllable input to a generator | SEC-05 |
| M-02 | Explicit source-ID stability scheme | Fragile IDs silently break citations | FR-10 + [08](08_DATA_MODELS_AND_API_CONTRACTS.md#4-identity-and-id-scheme) |
| M-03 | Upload size / page-count limits | A decompression-bomb PDF is an easy resource attack | SEC-02, SEC-03 |
| M-04 | Contradiction detection, not just low similarity | "Needs Review" and "Unsupported" need different triggers | FR-38 |
| M-05 | Support for absent optional model dependencies | Stage 2 lists it in Table 3 but no mechanism is specified | FR-31 |
| M-06 | Filename sanitisation for display | Filenames come from untrusted uploads | SEC-01 |
| M-07 | A defined abstention mechanism | "Say I don't know" is the honest failure mode | FR-33 |
| M-08 | Accessibility requirements for the verification panel | Colour-only encoding fails colour-blind users | FR-45, NFR-10 |
| M-09 | Performance measurement procedure | Stage 2 promises "record indexing and response time" but defines no method | NFR-07→09, [10](10_EVALUATION_METRICS.md) |
| M-10 | Determinism requirement stated as a testable NFR | Stage 2 Table 7 states it as an intent | NFR-03 |

## 4. What must be built (Phase 2 onwards)

Ordered by dependency. Full detail in [06_IMPLEMENTATION_ROADMAP.md](06_IMPLEMENTATION_ROADMAP.md).

| Order | Deliverable | Modules | Requirements |
|---|---|---|---|
| 1 | Environment + pinned deps | `requirements.txt` | C4, NFR-05 |
| 2 | Typed models | `src/models.py` | [08](08_DATA_MODELS_AND_API_CONTRACTS.md) |
| 3 | PDF validation + extraction | `src/pdf_ingestion.py` | FR-01→10 |
| 4 | Sentence-aware chunking | `src/chunking.py` | FR-11→15 |
| 5 | Embedding backends | `src/embeddings.py` | FR-16→18 |
| 6 | Vector stores | `src/vector_store.py` | FR-19→22 |
| 7 | Retrieval + stable source mapping | `src/vector_store.py` | FR-23→28 |
| 8 | Extractive + optional abstractive generation | `src/generator.py` | FR-29→33 |
| 9 | Citation verification | `src/verifier.py` | FR-34→40 |
| 10 | Orchestration | `src/pipeline.py` | NFR-11 |
| 11 | Streamlit UI | `app.py` | FR-41→47 |
| 12 | CLI demo | `run_demo.py` | FR-48 |
| 13 | Test suite | `tests/test_core.py` | All of [09](09_TESTING_STRATEGY.md) |
| 14 | Labelled evaluation set + metrics | `tests/`, `docs/` | NFR-07→09 |
| 15 | Screenshots, logs, viva script | `docs/` | Phase 7 |

## 5. Open risks originating in this audit

| Risk | Description | Register |
|---|---|---|
| Python version | Only 3.14.6 available; Stage 2 pinned 3.13.5. `chromadb 1.5.9` ships a `cp39-abi3-win_amd64` wheel (forward-compatible, so it *should* install on 3.14) but this is unverified on this machine. | [R-01](14_RISK_REGISTER.md) |
| Unverifiable historical numbers | 10/10 tests, 28 chunks, 11 pages, 4 commit hashes — none reproducible. High temptation to reuse them in Stage 3. | [R-02](14_RISK_REGISTER.md) |
| Missing 20-case set | Stage 1 claims the cases were "already prepared beforehand". They are not in the workspace. Phase 6 must create them without predetermining results. | [R-03](14_RISK_REGISTER.md) |
| Stage 2 citation mis-numbering | I-01 **checked in Phase 7 and not reproduced** — Stage 2's numbering is self-consistent. Stage 3 cites only what it read. | [R-04, closed](14_RISK_REGISTER.md) |
| Time | Planning must not consume the 3–5 day build budget. | [R-05](14_RISK_REGISTER.md) |

## 6. Audit conclusion

The project is **greenfield with a strong written specification**. That is a better starting position
than it first appears: Stage 2 has already resolved the hard design arguments (chunk size, label
semantics, threshold configurability, pypdf vs PyPDF2, the two-profile approach), so Phase 2 is
execution rather than re-litigation.

But it also means the entire engineering evidence base for Stage 3 must be created from scratch. The
single most important discipline for this project from here is: **measure it, then write it down.**