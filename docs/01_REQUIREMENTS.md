# 01 — Requirements

**Status:** Phase 1 baseline · Last updated 2026-10-08
**Related:** [Charter](00_PROJECT_CHARTER.md) · [Architecture](04_SYSTEM_ARCHITECTURE.md) · [Testing](09_TESTING_STRATEGY.md) · [Gap Analysis](03_GAP_ANALYSIS.md)

Requirement IDs are stable. Code and docs reference these IDs. Never renumber; mark as superseded and
add a new one.

---

## 1. Requirement conventions

| Attribute | Values |
|---|---|
| Type | `FR` functional · `NFR` non-functional · `SEC` security · `CON` constraint |
| Priority | `P0` MVP-must · `P1` important · `P2` nice · `P3` stretch |
| Phase | The phase that delivers it: 2, 3, 4, 5, 6, 7 |
| Status | `Planned` · `Implemented` · `Verified` · `Measured` · `Blocked` |

**Status as of 2026-10-08, after Phase 3.** Everything from Phases 4–7 is still `Planned`. The
Phase 2 and Phase 3 items are `Verified` — code exists **and** a command was run with its real output
observed. Two metrics are `Measured` (indexing and query latency, offline profile only).

| Verified in Phase 2 | Delivered in |
|---|---|
| FR-02 → FR-06, FR-08 → FR-14 | `src/pdf_ingestion.py`, `src/chunking.py`, `src/models.py` |
| SEC-01 → SEC-04, SEC-06 → SEC-08 | `src/pdf_ingestion.py`, `.gitignore`, suite |
| SEC-05 | detection only; end-to-end defence is Phase 4 |

| Verified in Phase 3 | Delivered in |
|---|---|
| FR-01, FR-07, FR-16, FR-18 → FR-28 | `src/pipeline.py`, `src/embeddings.py`, `src/vector_store.py` |
| FR-20 → FR-22 | `src/vector_store.py` |
| EC-05, EC-08, EC-15 (persistence half) | `src/pipeline.py`, `src/vector_store.py` |

| Still `Planned` | Why |
|---|---|
| FR-15, FR-17 | `index_stats()` exists (FR-15's mechanism); its reportability and MiniLM's 384 dims need Phase 4/6 |
| FR-29 → FR-50 | Phase 4 onwards — generation, verification, UI, reproducibility |
| NFR-01 → NFR-12 | Phase 6, except NFR-05 (verified via the clean-venv install) |
| SEC-05 (end-to-end) | Phase 4 — the verifier must exist before it can be attacked |

---

## 2. Functional requirements

### 2.1 Ingestion and validation

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-01 | Accept one or more `.pdf` uploads | P0 | 2 | Two files uploaded in one action both reach the index; library shows 2 rows | Stage 2 §2.1.1 |
| FR-02 | Reject non-PDF extensions before any parsing | P0 | 2 | `PDFIngestionError` raised; message names PDF-only | Stage 2 Table 3 |
| FR-03 | Reject zero-byte and empty PDFs | P0 | 2 | `PDFIngestionError`; no index created | Stage 2 Table 3 |
| FR-04 | Detect and reject password-protected PDFs | P0 | 2 | Message explains passwords unsupported; no partial index | Stage 2 Table 3 |
| FR-05 | Detect structurally-invalid PDFs | P0 | 2 | `pypdf` parse failure surfaced as `PDFIngestionError` with cause | Stage 2 §2.1.1 |
| FR-06 | Detect scanned/image-only PDFs and state the OCR limitation | P0 | 2 | After both parsers yield no usable text, message explicitly says OCR is required and out of scope | Stage 2 Table 3 |
| FR-07 | Enforce a page-count limit and warn beyond it | P1 | 2 | Configurable `max_pages`; warning names the operating target, not a guarantee | Stage 2 Table 1 |
| FR-08 | Extract text page-by-page with `pypdf` | P0 | 2 | Page count matches the PDF; page numbers preserved 1-based | Stage 2 §2.1.1 |
| FR-09 | Fall back to `pdfplumber` for pages with little extractable text | P0 | 2 | A page that `pypdf` returns near-empty for is re-extracted; result improves or is kept | Stage 2 §2.1.1 |
| FR-10 | Preserve filename, real page number, text and a stable source ID per page | P0 | 2 | Every `DocumentPage` has all four; IDs identical across re-runs | Stage 2 §2.1.2 |

### 2.2 Chunking

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-11 | Sentence-aware chunking, default ~180 words | P0 | 2 | Chunks end at sentence boundaries where possible | Stage 2 §2.1.2 |
| FR-12 | Configurable overlap, default 30 words | P0 | 2 | Consecutive chunks share exactly the configured number of words | Stage 2 §2.1.2 |
| FR-13 | Reject invalid chunk configuration (overlap ≥ size, non-positive size) | P0 | 2 | `ValueError`; test covers overlap == size | Stage 2 TC-04 |
| FR-14 | Every chunk inherits page + filename metadata | P0 | 2 | Chunk metadata resolves to the correct page of the correct file | Stage 2 TC-03 |
| FR-15 | Chunk count and word-count distribution are reportable | P2 | 2 | `index_stats()` returns chunk count, page count, doc count | Stage 3 evidence need |

> **Why 180/30 and not 500/50 (Stage 1):** `all-MiniLM-L6-v2` has an effective `max_seq_length` of
> **256** word-piece tokens (verified via the Hugging Face API, 2026-10-08). A 500-token chunk is
> truncated by roughly half, so the stored embedding silently represents only the first portion of
> the evidence. ~180 English words ≈ 230–240 word-pieces, which fits. This is a *correctness* reason,
> not a preference, and it is the single most defensible technical decision in the project.

### 2.3 Embedding and indexing

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-16 | Provide an embedding backend interface with two implementations | P0 | 3 | Semantic backend and TF-IDF backend satisfy one protocol | Stage 2 §2.1.3 |
| FR-17 | Semantic backend uses `all-MiniLM-L6-v2` | P1 | 3 | Embeddings are 384-dim unit vectors | Stage 2 Table 4 |
| FR-18 | TF-IDF backend requires no model download and no network | P0 | 3 | Works with `HF_HUB_OFFLINE=1` and no internet | Stage 2 §1.1 |
| FR-19 | Persist vectors + metadata locally in Chroma | P1 | 3 | Second process run queries the same index without re-embedding | Stage 2 §2.1.3 |
| FR-20 | Deterministic in-memory store for tests | P0 | 3 | Same chunks + same query ⇒ byte-identical ranking, no network | Stage 2 §2.1.3 |
| FR-21 | Prevent index construction from an empty chunk set | P0 | 3 | Clear error, no empty collection created | Stage 2 Table 3 |
| FR-22 | Support re-indexing and document removal without corrupting state | P1 | 3 | Remove a doc → it no longer appears in retrieval; re-add → returns | Prompt mandate |

### 2.4 Retrieval

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-23 | Reject a blank/whitespace-only query before retrieval | P0 | 3 | `ValueError`; no vector search performed | Stage 2 TC-09 |
| FR-24 | Return top-k most relevant chunks, default `k=5` | P0 | 3 | Result count == `min(top_k, chunk_count)` | Stage 2 TC-05/06 |
| FR-25 | Clamp `top_k` to collection size instead of erroring | P0 | 3 | `top_k=10` with 3 chunks returns 3 | Stage 2 TC-06 |
| FR-26 | Retrieval score is stored and exposed **separately** from support score | P0 | 3 | Two distinct fields; never averaged or conflated | Stage 2 §7.2 |
| FR-27 | Deterministic tie-breaking for equal scores | P1 | 3 | Repeated identical queries give identical ordering | Reproducibility NFR |
| FR-28 | Map every retrieved chunk back to filename + real page | P0 | 3 | `RetrievalResult.page` matches the source PDF page | Stage 2 TC-10 |

### 2.5 Generation

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-29 | Generator receives **only** retrieved evidence, never the whole corpus | P0 | 4 | Generator signature takes the evidence list; no corpus access | Stage 2 §2.1.4 |
| FR-30 | Deterministic extractive generator works with no model downloads | P0 | 4 | Same evidence ⇒ same answer text, offline | Stage 2 §1.1 |
| FR-31 | Optional FLAN-T5-small adapter, opt-in and degradable | P2 | 4 | Missing weights ⇒ explicit message, system still works | Stage 2 Table 3 |
| FR-32 | Every factual sentence carries a `[Sx, p.y]` marker | P0 | 4 | 100% of extracted claim sentences have ≥1 marker | Stage 2 Table 7 |
| FR-33 | Absent/insufficient evidence ⇒ explicit abstention, never an invented answer | P0 | 4 | Empty retrieval yields an abstention message | Prompt mandate |

### 2.6 Citation verification

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-34 | Parse every `[Sx, p.y]` marker with a strict regex | P0 | 4 | Markers found deterministically; malformed markers flagged, not guessed | Stage 2 §2.1.5 |
| FR-35 | Resolve each marker against the *retrieved* set only | P0 | 4 | A marker pointing at a non-retrieved chunk is `Unsupported` | Stage 2 Table 3 |
| FR-36 | Compute `support_score` per Stage 2 formula | P0 | 4 | `0.7 * sim + 0.3 * overlap`, both components normalised to [0,1] | Stage 2 §2.1.5 |
| FR-37 | Assign `Verified` / `Needs Review` / `Unsupported` from configurable thresholds | P0 | 4 | Thresholds from config, never literals inside the scorer | Stage 2 §2.1.5 |
| FR-38 | Detect and label contradictory claims as `Unsupported` | P0 | 4 | Negated/contradicted claim against its cited passage ⇒ `Unsupported` | Prompt mandate |
| FR-39 | Expose score, components, and a human-readable explanation per claim | P0 | 4 | Evidence inspector shows all three | Prompt mandate |
| FR-40 | Keep support score strictly distinct from retrieval relevance score | P0 | 4 | No code path averages them | Stage 2 §7.2 |

### 2.7 UI

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-41 | Dashboard: identity, value proposition, live collection stats, upload zone | P1 | 5 | Stats read from the live index, not hardcoded | Prompt §6 |
| FR-42 | Document library: filename, page count, chunk count, index status, remove/reindex | P1 | 5 | Rows reflect the real index | Prompt §6 |
| FR-43 | Research workspace: question input, answer, markers, verification summary | P1 | 5 | Answer rendered with clickable markers | Prompt §6 |
| FR-44 | Evidence inspector: file, page, passage, status, score, explanation | P1 | 5 | Selecting a marker opens its real passage | Prompt §6 |
| FR-45 | Verification panel with accessible colour **plus** text label **plus** symbol | P1 | 5 | Colour-blind readable; labels are text, not colour alone | Prompt §6 |
| FR-46 | Graceful states for upload, parse, index, model load, retrieve, generate, verify, empty, missing model, failure | P1 | 5 | Each state designed and reachable | Prompt §6 |
| FR-47 | UI calls pipeline APIs only; no duplicated retrieval or scoring logic | P0 | 5 | No scoring/threshold literals in `app.py` | Stage 2 §2.3 |

### 2.8 Reproducibility

| ID | Requirement | Priority | Phase | Acceptance criteria | Source |
|---|---|---|---|---|---|
| FR-48 | `run_demo.py` performs a full reproducible CLI run | P0 | 6 | Index → ask → verify → exit code, printed with timings | Stage 2 §3.2 |
| FR-49 | Same PDF + same query ⇒ identical fallback output | P0 | 6 | Regression test asserts byte-equality across two runs | Stage 2 Table 7 |
| FR-50 | `index_stats()` and per-query timings are available for the report | P1 | 6 | Metrics collectible without instrumenting ad hoc | Stage 3 evidence need |

## 3. Stage 2 versus Stage 1 deviations log

Stage 2 overrides Stage 1. This log is the audit trail; do not silently discard any row.

| # | Stage 1 said | Stage 2 says | Rationale | Status |
|---|---|---|---|---|
| D-01 | LangChain is the "LLM / Framework" | LangChain removed; generator is `google/flan-t5-small`; orchestration is direct Python | LangChain is an orchestration framework, not a language model. Listing it as the LLM was factually wrong. | Implemented in Stage 3 design; **carried forward** |
| D-02 | ~500 tokens/chunk, 50-token overlap | ~180 words/chunk, 30-word overlap | Stage 1 mixed units *and* exceeded MiniLM's effective input length. Verified: `all-MiniLM-L6-v2` `max_seq_length = 256`. See FR-15. | **Carried forward, now evidence-backed** |
| D-03 | Labels: Verified / Unverified / Hallucinated | Verified / Needs Review / Unsupported | Cosine similarity measures relatedness, not truth. "Hallucinated" is an interpretation requiring evaluation, not a system output. | **Carried forward** |
| D-04 | Fixed thresholds 0.75 / 0.40 treated as proof | Configurable thresholds, calibrated on a manually labelled set | Thresholds are configuration, not universal constants. | **Carried forward** — see [10_EVALUATION_METRICS.md](10_EVALUATION_METRICS.md) |
| D-05 | `PyPDF2` | `pypdf` primary, `pdfplumber` fallback | `PyPDF2` is the deprecated name; `pypdf` is the maintained successor. | **Carried forward** |
| D-06 | "LLM Generator" block, no model named | `google/flan-t5-small` (optional) | A concrete, small, commercially-free local model was required for defensibility. | **Carried forward** |
| D-07 | SDG 4 + SDG 9 + SDG 16 as primary claims | SDG 4 primary, SDG 9 secondary, SDG 16 explicitly indirect | SDG 16 as a primary measurable claim was an overreach. | **Carried forward** |
| D-08 | "up to 50 papers" as a scope guarantee | Configurable operating target, not a guarantee | Actual capacity depends on page count, extraction quality, RAM, index size. | **Carried forward** |
| D-09 | (absent) | Two explicit profiles: semantic + offline validation | Makes ingestion, retrieval, citation formatting, verification and testing demonstrable before any model download. | **Carried forward** — drives FR-18/FR-20 |
| D-10 | (absent) | Python 3.13.5 named as the Stage 2 validation interpreter | **Amended to 3.14.6 in Phase 2.** Only 3.14.6 exists on the machine; the pin is a human decision recorded in [ADR-0001](05_TECH_STACK_AND_ADRS.md#adr-0001--pin-the-python-version). Stage 2's real constraint was "3.10 or newer", so this is a superset, not a violation | **Amended in Phase 2** |

> D-10 note, resolved: the human team lead pinned **CPython 3.14.6** on 2026-10-08 and
> `chromadb` 1.5.9 was installed and proven to persist on it, so the compatibility question behind
> the original open item is now closed by execution rather than by prediction. See
> [ADR-0001](05_TECH_STACK_AND_ADRS.md#adr-0001--pin-the-python-version) and
> [R-01, retired](14_RISK_REGISTER.md).

## 4. Non-functional requirements

| ID | Requirement | Metric | Target | Verification method |
|---|---|---|---|---|
| NFR-01 | Offline capability | Works with no network, no API key | Must pass | Test with network disabled + `HF_HUB_OFFLINE=1` |
| NFR-02 | CPU-only operation | No CUDA required | Must pass | Run on CPU; record it |
| NFR-03 | Determinism (fallback) | Identical output across runs | 100% | Byte-comparison regression test |
| NFR-04 | Test coverage of mandated scenarios | 17 scenarios | 17/17 | [09_TESTING_STRATEGY.md](09_TESTING_STRATEGY.md) checklist |
| NFR-05 | Single-command install | `pip install -r requirements.txt` in a clean venv | Must pass | Fresh-venv check |
| NFR-06 | Startup responsiveness | App interactive without model download | < 5 s | Stopwatch, recorded |
| NFR-07 | Query latency (fallback profile) | p95 over 20 queries | Record, not a promise | Measured in Phase 6 |
| NFR-08 | Indexing latency | Per 100 pages | Record, not a promise | Measured in Phase 6 |
| NFR-09 | Peak RAM | Whole pipeline | Record, not a promise | Measured in Phase 6 |
| NFR-10 | Accessibility | Contrast + text labels + keyboard | WCAG AA target for text | Manual contrast check in Phase 5 |
| NFR-11 | Module independence | Each `src/` module unit-testable alone | Must pass | No import of `pipeline` inside leaf modules |
| NFR-12 | No fabricated data | Zero hardcoded stats/claims in UI | Must pass | Grep for placeholder patterns; manual review |

> NFR-07/08/09 are deliberately "record, not promise". Promising a latency without measuring it is
> exactly the failure mode this project is criticising.

## 5. Security requirements

| ID | Requirement | Acceptance criteria |
|---|---|---|
| SEC-01 | Uploaded filenames sanitised before display | No path traversal, no control characters, length-capped |
| SEC-02 | Upload size limit enforced | Configurable `max_upload_mb`; oversized rejected before parsing |
| SEC-03 | Page-count limit enforced | Prevents memory exhaustion on a decompression-bomb PDF |
| SEC-04 | No code execution from PDF content | Extracted text is only ever rendered/escaped, never `eval`'d or `exec`'d |
| SEC-05 | **Prompt-injection defence** | PDF text is treated as untrusted *evidence*. Injection-shaped text (e.g. "ignore previous instructions", "you are now…") is detected, flagged in the UI, and never executed as instruction. See [Architecture §7](04_SYSTEM_ARCHITECTURE.md#7-untrusted-content-and-prompt-injection). |
| SEC-06 | No secrets in the repo | No API keys, no `.env` committed, no credentials in code |
| SEC-07 | Index stored inside the project dir | No writes outside the project workspace |
| SEC-08 | No network calls in the default path | Verified by test |

## 6. Edge cases (must be handled, not merely considered)

| ID | Edge case | Required behaviour |
|---|---|---|
| EC-01 | Wrong file type | Reject before parsing with a PDF-only message |
| EC-02 | Zero-byte PDF | Reject; do not create an empty index |
| EC-03 | Encrypted PDF | Stop with an explanation; never a partial index |
| EC-04 | Scanned/image-only PDF | Clear OCR-required message |
| EC-05 | Blank question | Reject before retrieval |
| EC-06 | Empty document / zero chunks | Prevent index construction; clear error |
| EC-07 | `overlap >= chunk_size` | `ValueError` |
| EC-08 | `top_k` > collection size | Clamp, return what exists |
| EC-09 | Valid citation mapping | Resolves to real file + page |
| EC-10 | Fabricated/invalid marker | `Unsupported` |
| EC-11 | Supported paraphrase | `Verified` |
| EC-12 | Unsupported or contradictory claim | `Unsupported` |
| EC-13 | Missing optional model dependency | Message + working fallback, never a silent crash |
| EC-14 | Multi-document citations | Correct per-document source IDs |
| EC-15 | Repeated indexing / persistence | Stable IDs, no duplication |
| EC-16 | Empty retrieval / insufficient evidence | Abstain |
| EC-17 | Offline, no API key | Full fallback workflow works |

Full test design per case: [09_TESTING_STRATEGY.md](09_TESTING_STRATEGY.md).

## 7. Out-of-scope register (do not implement without approval)

| ID | Excluded | Why | Would need |
|---|---|---|---|
| OOS-01 | OCR | Explicitly excluded in Stage 2; heavy dependency | Approval + time |
| OOS-02 | NLI / cross-encoder verifier | Stage 2 Table 12 lists this as future work | Phase ≥ 6 + calibration budget |
| OOS-03 | Live arXiv/Scopus scraping | Stage 1 §1.3 out-of-scope | Approval |
| OOS-04 | Paid API generation | C1 forbids | Approval |
| OOS-05 | Multi-turn conversation memory | Not in Stage 2 scope | Approval |
| OOS-06 | React/Next.js/FastAPI replacement | C6 forbids | Approval |
| OOS-07 | Agentic self-correction loops | Unnecessary complexity for this scope | Approval |
| OOS-08 | Citation export (BibTeX/Zotero) | P3 | Approval |
| OOS-09 | Authentication / multi-user | Not in scope | Approval |

## 8. Traceability matrix: requirement, phase, evidence

The `Evidence` column is filled only when a real artifact exists. A cell is written only after a
command was run and its output observed — that is the mechanism that prevents fabricated report
claims. Full detail: [12_STAGE_3_EVIDENCE_TRACKER.md](12_STAGE_3_EVIDENCE_TRACKER.md).

| Phase | Requirements | Gate | Evidence status |
|---|---|---|---|
| 2 | FR-01→FR-15, FR-21, SEC-01→04 | Ingestion+chunking tests pass | **Gate G2 passed.** 12 FR + 7 SEC verified by `pytest -q` → 56 passed. FR-01/07/15 and FR-21 land in Phase 3; SEC-05 detection only |
| 3 | FR-16→FR-28 | Retrieval tests pass, offline path green | **Gate G3 passed.** 13 FR verified by `pytest -q` → 144 passed. FR-15 and FR-17 unmeasured |
| 4 | FR-29→FR-40 | Verification tests pass, abstention works | **Gate G4 passed.** 12 FR + 6 CT verified by `pytest -q` → 227 passed. FLAN-T5 success path unmeasured |
| 5 | FR-41→FR-47, NFR-10 | All UI states render real data | **Gate G5 passed.** 7 FR + 98 UI tests; headless HTTP 200; 13 contrast ratios measured. 3 manual visual checks pending (R-23) |
| 6 | FR-48→FR-50, NFR-01→09, NFR-11 | Full suite green + metrics measured | **Gate G6 passed except CI.** `pytest -q` → **371 passed, 6 deselected**; 13 metrics measured on the real report; 46 hardening tests. CI cannot run — no repository (B-08). NFR-01's semantic half unmeasured |
| 7 | — | Evidence tracker complete, demo rehearsed | *empty — not built* |