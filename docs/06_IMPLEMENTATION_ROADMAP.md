# 06 — Implementation Roadmap

**Status:** Phase 1 baseline · Last updated 2026-10-08
**Related:** [Charter](00_PROJECT_CHARTER.md) · [Requirements](01_REQUIREMENTS.md) · [Progress Tracker](15_PROGRESS_TRACKER.md) · [Testing](09_TESTING_STRATEGY.md)

---

## 1. Scheduling philosophy

The build is **dependency-ordered, not time-ordered**. Ingestion and chunking must be trustworthy
before retrieval can be measured; retrieval must return page-accurate evidence before verification
means anything; the UI comes after the pipeline API is stable. This ordering is inherited from
Stage 2 §6.1 and is deliberate — it stops the team polishing a front end over a moving foundation.

Timeboxes are **estimates for planning, not commitments**, and they assume three people working in
parallel. The total build budget is 3–5 focused days.

**The single most important scheduling rule: the deterministic fallback profile must be working and
tested before any model download is attempted.** If the deadline arrives with no models downloaded,
the project is still demonstrable.

## 2. Phase overview

| Phase | Name | Estimate | Owner (lead) | Gate |
|---|---|---|---|---|
| 0 | Research + audit | **done** | All | This documentation set |
| 1 | Documentation | **done** | All | This documentation set |
| 2 | Foundation + PDF processing | **done** (0.5–0.75 d) | Bhavya (ingestion), Purv (models/chunking) | G2 **passed** |
| 3 | Retrieval | **done** (0.5–0.75 d) | Purv | G3 **passed** |
| 4 | Generation + verification | **done** (0.75–1 d) | Rishabh (verifier), Purv (generator) | G4 **passed** |
| 5 | Premium UI | **done** (0.75–1 d) | Purv | G5 **passed** (3 manual items pending) |
| 6 | Testing + hardening | **done** (0.5–0.75 d) | Bhavya | G6 **passed** (CI cannot run — no repo) |
| 4 | Generation + verification | 0.75–1 d | Rishabh (verifier), Purv (generator) | G4 |
| 5 | Premium UI | 0.75–1 d | Purv | G5 |
| 6 | Testing + hardening | 0.5–0.75 d | Bhavya | G6 |
| 7 | Stage 3 readiness | 0.5 d | All | G7 |

## 3. Phase 2 — Foundation + PDF Processing

**Owner:** Bhavya (ingestion), Purv (models + chunking) · **Review:** Rishabh
**Delivers:** FR-01→FR-15, FR-21, SEC-01→SEC-04, ADR-0001, ADR-0003

### Scope

| # | Item | File |
|---|---|---|
| 2.1 | Resolve the Python pin (ADR-0001) and create `.venv` | — |
| 2.2 | `requirements.txt` with pinned versions; verify clean-venv install | `requirements.txt` |
| 2.3 | Typed dataclasses: `DocumentPage`, `EvidenceChunk`, `IndexReport` | `src/models.py` |
| 2.4 | `PDFIngestionError` hierarchy | `src/pdf_ingestion.py` |
| 2.5 | Validate: extension, existence, size, empty, encrypted, structure | `src/pdf_ingestion.py` |
| 2.6 | `pypdf` page extraction | `src/pdf_ingestion.py` |
| 2.7 | `pdfplumber` per-page fallback on near-empty pages | `src/pdf_ingestion.py` |
| 2.8 | Scanned-document detection + OCR-limitation message | `src/pdf_ingestion.py` |
| 2.9 | Deterministic stable source-ID scheme | `src/pdf_ingestion.py` |
| 2.10 | Filename sanitisation + injection-pattern warning | `src/pdf_ingestion.py` |
| 2.11 | Regex sentence splitter | `src/chunking.py` |
| 2.12 | Chunking with overlap + config validation | `src/chunking.py` |
| 2.13 | Page→chunk metadata inheritance | `src/chunking.py` |
| 2.14 | Tests: EC-01→EC-07, EC-14, EC-15, FR-13 | `tests/test_core.py` |

### Explicitly NOT in Phase 2

Embeddings, vector stores, retrieval, generation, verification, UI, Chroma install. If time is short,
Phase 2 must still deliver a *complete, tested* ingestion→chunking slice, not a partial one.

### Rollback / fallback

- If `pypdf` fails on a file, the error must name the file and the cause. No silent skip.
- If sentence splitting proves inadequate on the fixture, chunk size shrinks — **never** abandon
  sentence-awareness silently; record it in the tracker.

### Gate G2

**Result: PASSED 2026-10-08.** Evidence for each box is in
[15_PROGRESS_TRACKER.md §7](15_PROGRESS_TRACKER.md#7-test-results) and §8.

- [x] Python version pinned and recorded in ADR-0001 — CPython 3.14.6, accepted
- [x] Clean venv installs from `requirements.txt` without manual intervention — 110 packages, one command
- [x] All EC-01→EC-07 tests pass with real output — `pytest -q` → 56 passed (EC-06 partial by design, see below)
- [x] `DocumentPage` carries source_id, filename, page, text for every page of the fixture — 5/5 pages
- [x] Chunking preserves page metadata for every chunk — asserted in `TestChunking` / `TestContracts`
- [x] `overlap >= chunk_size` raises `ValueError` — also rejects `>` and non-positive sizes
- [x] Scanned-PDF path produces the OCR message (tested with a synthetic fixture) — graphics-only 3-page PDF
- [x] Measured page/chunk counts recorded in the progress tracker — 5 pages → 5 chunks, 48 words

Two honest qualifications, recorded rather than glossed:

1. **EC-06 is only half delivered.** `chunk_pages` on an empty page set returns `()` and that is
   tested. Refusing to *construct a store* from zero chunks is FR-21, which Phase 3 delivers. The
   Phase 2 half is the observable the Phase 3 test will assert against.
2. **SEC-03's fixture is 15 pages, not 5,000.** The limit branch is identical; a 5,000-page fixture
   would cost a hundred times the build time for no extra coverage. Noted in the test itself.

Also done early, deliberately: item **3.10** (`chromadb` install and smoke test) moved forward into
Phase 2 (decision D-12), because knowing the answer before designing against it retires
[R-01](14_RISK_REGISTER.md) at almost no cost. Result: `chromadb` 1.5.9 imports, stores, queries and
reloads on CPython 3.14.6.

## 4. Phase 3 — Retrieval

**Owner:** Purv (lead) · **Review:** Rishabh
**Delivers:** FR-16→FR-28

### Scope

| # | Item | File |
|---|---|---|
| 3.1 | `EmbeddingBackend` protocol + `TfidfEmbeddingBackend` | `src/embeddings.py` |
| 3.2 | `MiniLMEmbeddingBackend` (lazy, cached, graceful if unavailable) | `src/embeddings.py` |
| 3.3 | `InMemoryVectorStore` — deterministic, test-first | `src/vector_store.py` |
| 3.4 | `ChromaVectorStore` — persistent adapter | `src/vector_store.py` |
| 3.5 | `add()`, `query()` with `top_k` clamping | `src/vector_store.py` |
| 3.6 | `RetrievalResult` with **separate** relevance score | `src/models.py` |
| 3.7 | Blank-query rejection | `src/pipeline.py` |
| 3.8 | Empty-collection guard | `src/pipeline.py` |
| 3.9 | Persistence + re-index + remove-document tests | `tests/test_core.py` |
| 3.10 | Install and smoke-test `chromadb` on the pinned Python | — |

### Explicitly NOT in Phase 3

Generation, verification, UI, rerankers, hybrid BM25+dense search, cross-encoders. Hybrid retrieval is
**not** in scope — Stage 2 specifies dense + a TF-IDF fallback profile, and adding RRF fusion is a
P2 enhancement that would need its own justification.

### Rollback / fallback

- If `chromadb` will not install on the pinned Python (ADR-0001 risk), ship the in-memory store as the
  *only* persistence mechanism, log it in [R-01](14_RISK_REGISTER.md), and adjust the Stage 3 report
  honestly. Do **not** silently drop persistence from the report.
- If MiniLM download fails, the TF-IDF profile must keep every Phase 3 test green.

### Gate G3

**Result: PASSED 2026-10-08.** Evidence in
[15_PROGRESS_TRACKER.md §7](15_PROGRESS_TRACKER.md#7-test-results) and §8.

- [x] TF-IDF profile works with `HF_HUB_OFFLINE=1` and no network — 144 passed with the hub disabled
- [x] `top_k=10` with 3 chunks returns exactly 3 (EC-08) — and IR-4 is asserted at 1/3/10/50
- [x] Blank query raises `ValueError` **before** any search (EC-05) — tested with the store replaced by a function that raises if called
- [x] Empty chunk set is refused (EC-06) — `_retrieve` on an empty index raises `ValueError`; `index()` on zero chunks yields a `zero_chunks` failure
- [x] Retrieval relevance score is a distinct field from anything called "support" — CT-08 asserts the *absence* of `support_score`, plus that no field name contains "support"
- [x] Second process run reuses the persisted index without re-embedding (EC-15) — proven with `load_document` monkeypatched to raise; the restart reads no PDF at all
- [x] Document removal removes it from retrieval — FR-22, asserted in both stores
- [x] `chromadb` import status recorded honestly — 1.5.9, working, verified in Phase 2

Three honest qualifications:

1. **`ask()` does not exist yet.** Retrieval is `pipeline._retrieve`, a private method. `ask()`
   arrives in Phase 4 with the generator and verifier it needs. EC-05 and the empty-index guard
   are implemented and tested at the layer `ask()` will delegate to, so neither is re-implemented
   later. Decision D-16.
2. **A degraded profile cannot score its own earlier vectors.** If MiniLM is configured, fails to
   load mid-session, and the pipeline falls back to TF-IDF, the chunks already embedded by MiniLM
   are *not* comparable to TF-IDF queries. Those chunks are counted in `stale_chunks` and reported
   rather than silently returned as if they had been scored by the profile now running. Rebuilt
   only by a fresh re-index.
3. **The 4 semantic-marked tests are deselected by default and were not run.** They need MiniLM
   weights, which are not on this machine. They are written and importable; their result is
   *unmeasured*, not passed. See §7 of the progress tracker.

## 5. Phase 4 — Generation + Verification

**Owner:** Rishabh (verifier, lead for the scoring core), Purv (generator)
**Delivers:** FR-29→FR-40 — **the project's core contribution**

### Scope

| # | Item | File |
|---|---|---|
| 4.1 | `VerificationConfig` (thresholds, weights, stopwords, antonyms) | `src/models.py` |
| 4.2 | Extractive grounded generator — default path | `src/generator.py` |
| 4.3 | Marker attachment from **retrieved data only** | `src/generator.py` |
| 4.4 | FLAN-T5-small adapter — optional, greedy, degradable | `src/generator.py` |
| 4.5 | Marker parser (strict regex) | `src/verifier.py` |
| 4.6 | Marker → retrieved-set resolution; unresolvable ⇒ Unsupported | `src/verifier.py` |
| 4.7 | `token_overlap` (containment, stopword-filtered) | `src/verifier.py` |
| 4.8 | Similarity component, per profile, normalised to [0,1] | `src/verifier.py` |
| 4.9 | `support_score = 0.7*sim + 0.3*overlap` | `src/verifier.py` |
| 4.10 | Number-consistency check | `src/verifier.py` |
| 4.11 | Negation + antonym contradiction checks | `src/verifier.py` |
| 4.12 | Label assignment from config thresholds | `src/verifier.py` |
| 4.13 | `ClaimVerification` with components, score, reason, explanation | `src/models.py` |
| 4.14 | Abstention when retrieval is empty | `src/pipeline.py` |
| 4.15 | Tests: EC-09→EC-13, EC-16, EC-17 | `tests/test_core.py` |

### Explicitly NOT in Phase 4

Re-attribution (ADR-0008), NLI models, cross-encoder scoring, citation export, multi-turn memory.

### Rollback / fallback

- If FLAN-T5 cannot be downloaded, the extractive generator is already the default — the demo is
  unaffected. Log it, do not apologise in the report.
- If contradiction checks produce false positives on the fixture, tighten them — do not delete them
  silently. Record the change in the decisions log.

### Gate G4

**Result: PASSED 2026-10-08.** Evidence in
[15_PROGRESS_TRACKER.md §7](15_PROGRESS_TRACKER.md#7-test-results) and §8.

- [x] Every extracted claim sentence carries ≥1 marker — asserted per claim, not per answer
- [x] Valid marker resolves to the correct filename and page (EC-09)
- [x] Fabricated marker `[S9, p.2]` when only S1 exists ⇒ `Unsupported`, reason `unresolvable_reference` (EC-10)
- [x] Supported paraphrase ⇒ `Verified` (EC-11)
- [x] Contradictory claim ⇒ `Unsupported`/`Needs Review` (EC-12)
- [x] Empty retrieval ⇒ abstention, no answer (EC-16)
- [x] Full offline run with no network and no API key (EC-17)
- [x] No numeric literal threshold inside any scoring function — a test greps `verifier.py` for `0.62`, `0.40`, `0.7 *`, `0.3 *`
- [x] Determinism: two identical offline runs give byte-identical output (EC-17)

Discrimination measured against a retrieved Chroma passage, so the labels are demonstrably doing
work rather than defaulting to `Verified`:

| Claim against the same passage | Label | Support | Reason |
|---|---|---|---|
| verbatim copy | Verified | 1.000 | `supported` |
| near paraphrase ("stores… locally, without any database server") | Verified | 0.632 | `supported` |
| correct words, **wrong page** | Unsupported | 0.000 | `page_mismatch` |
| **negation flipped** ("does not persist") | Needs Review | 0.000 | `contradiction_detected` |
| **wrong year** (2019 vs no date) | Unsupported | 0.000 | `numeric_mismatch` |
| unrelated (coral reefs) | Unsupported | 0.000 | `no_support` |
| **fabricated `[S7, p.1]`** | Unsupported | 0.000 | `unresolvable_reference` |
| **partially wrong** ("but requires a database server") | Needs Review | 0.000 | `contradiction_detected` |

Two honest qualifications:

1. **EC-11 uses a *lexical* paraphrase, not a synonym-substitution one.** "Overlap between consecutive
   chunks reduces the chance that a definition is split across a boundary" clears the threshold.
   "Making consecutive chunks share words lowers the risk of splitting a definition in half" scores
   **0.10** containment and is labelled `Unsupported`. That is the offline lexical profile being
   honest about the limit of its reach — a real finding for the report, not a bug to be papered over
   with an easier example. The semantic profile would plausibly follow the second; measuring that is
   Phase 6 work.
2. **The 6 `semantic`-marked tests were not run.** MiniLM and FLAN-T5 weights are absent. Their
   result is **unmeasured**.

## 6. Phase 5 — Premium UI

**Owner:** Purv (lead) · **Review:** Bhavya (states), Rishabh (verification panel)
**Delivers:** FR-41→FR-47, NFR-10, NFR-12

### Scope

| # | Item |
|---|---|
| 5.1 | Design tokens as CSS custom properties, namespaced |
| 5.2 | Sidebar navigation: Dashboard / Library / Workspace |
| 5.3 | Dashboard with **live** stats + upload zone |
| 5.4 | Document library with real filename, pages, chunks, status, remove/reindex |
| 5.5 | Research workspace: question, answer, markers, verification summary |
| 5.6 | Evidence inspector: file, page, passage, status, score, explanation |
| 5.7 | Verification panel: colour **+** text label **+** symbol |
| 5.8 | All activity/error states: uploading, parsing, indexing, model loading, retrieving, generating, verifying, empty, missing model, failure + recovery |
| 5.9 | Responsive layout + accessibility pass |
| 5.10 | Injection warning surfaced in the UI |

### Explicitly NOT in Phase 5

No invented statistics, no mock documents, no hardcoded verification results, no fake loading times.
If a panel has no real data to show, it shows an empty state.

### Rollback / fallback

If custom CSS destabilises Streamlit internals, reduce to the token set plus scoped card rules. A clean
readable UI beats a broken beautiful one.

### Gate G5

**Result: PASSED 2026-10-08, with three manual items outstanding.** Evidence in
[15_PROGRESS_TRACKER.md §7](15_PROGRESS_TRACKER.md#7-test-results).

Automated:

- [x] All six surfaces render with real backend data only — `TestRenderHelpersRun` (12 tests) drives each renderer with Streamlit stubbed and asserts the emitted markup
- [x] Every activity/error state is designed and reachable — each of the 10 ingest reason codes has tested recovery guidance; the abstention, degraded and stale-chunk states each have a test
- [x] Verification states distinguishable without colour (text + symbol) — chip renders icon + word + colour; tested that neither is removable
- [x] Text contrast meets the AA target — **measured**, 12 pairs, see §7b of the tracker
- [x] Keyboard reachable: nav, upload, question input, marker selection — markers are real `st.button`s, not clickable spans
- [x] No hardcoded statistics found by grep + review — UI-2 + the AST audit
- [x] CSS is namespaced; no global element selectors — every selector in the stylesheet is `.vs-*`, `:root` or `.stApp`
- [x] UI-1: `streamlit run app.py --server.headless true` serves HTTP 200, no traceback in the log
- [x] CT-20: `app.py` imports only `src.pipeline` and `src.models`
- [x] `prefers-reduced-motion` honoured; focus outline never removed; no looping animation

**Manual, not yet done — these need eyes on a real screen:**

- [ ] **Greyscale screenshot** — status legible with colour removed entirely (UI-4)
- [ ] **Keyboard-only walkthrough** — every control reachable in DOM order (UI-5)
- [ ] **1280 px and 768 px** — no horizontal scroll of the main column

These three are the reason the state is *pending manual verification* rather than *done*, and they
are Phase 7 screenshot work. Automated tests cannot tell you the layout looks right; claiming they
did would be exactly the overclaim this project exists to avoid.

Three notes on what building the UI changed in the design:

1. **Marker buttons are real Streamlit buttons, not clickable spans.** The spec's ASCII sketch
   implied clickable markers; a `<span onclick>` cannot be keyboard-activated, so the clickable-
   citation requirement would have been an accessibility lie. The visual treatment is the same chip
   style; the mechanism is a real widget.
2. **`app.py` imports nothing from a leaf module**, verified by CT-20. It reaches the system only
   through `ResearchPipeline` and the dataclasses.
3. **Four lookup tables are `MappingProxyType`, not dicts.** AGENTS.md forbids module-level mutable
   singletons, and the concrete risk is that a shared mutable table lets a later edit change what a
   label says with no test failing.

## 7. Phase 6 — Testing + Hardening

**Owner:** Bhavya (lead) · **All** contribute
**Delivers:** FR-48→FR-50, NFR-01→NFR-09, NFR-11

### Scope

| # | Item |
|---|---|
| 6.1 | Complete the 17-scenario suite; every case green |
| 6.2 | `run_demo.py` full reproducible CLI run |
| 6.3 | Offline verification run (network disabled) |
| 6.4 | Model-download and model-absent path tests |
| 6.5 | Security review: filename, size, page limits, injection, no `eval`/`exec` |
| 6.6 | Create the ≥20-case claim/evidence labelling set — **without predetermining results** |
| 6.7 | Run calibration; record the chosen thresholds with the precision/recall trade-off |
| 6.8 | Measure: model load, indexing latency, query latency p50/p95, peak RAM |
| 6.9 | Measure Recall@k on a small hand-built relevance set |
| 6.10 | GitHub Actions CI running `pytest -q` |
| 6.11 | Fresh-venv reproducibility check |

### Gate G6

**Result: PASSED 2026-10-08, with one requirement explicitly not met.** Evidence in
[15_PROGRESS_TRACKER.md §7](15_PROGRESS_TRACKER.md#7-test-results) and §7d.

- [x] `pytest -q` green, real output pasted into the tracker — **402 passed, 6 deselected**
- [x] EC-01→EC-17 all covered — 16 automated, 1 half-covered by design
- [x] Offline run proven with the network disabled — 402 passed with `socket.connect` replaced by a function that raises, then a full index→ask→verify cycle
- [x] Determinism regression test passes — 1.0 over 5 runs, excluding wall-clock timings (see below)
- [x] All metrics measured or explicitly marked *not measured* — 13 measured, 4 explicitly not
- [x] Thresholds justified by the labelled set, with the trade-off shown — `verified_threshold` moved 0.62 → **0.63**; sweep in §7d
- [x] Zero high-severity security findings — 46 hardening tests; the sweep found no `eval`/`exec`, no secrets, no network on the default path, no writes in `src/`
- [x] **CI green — PASSED 2026-10-09.** Run [37880879892](https://github.com/Purv-Jain/Aries/actions/runs/37880879892) on `66075b`: `offline (ubuntu-latest)`, `offline (windows-latest)` and `security-sweep` all **success**. The previous failure (run 37835567623 on `9772226`) was caused by `PROJECT_ROOT / r"tests\data\..."` resolving to a *single filename* on POSIX, so the nine `TestEvaluationSetIntegrity` tests raised `FileNotFoundError` instead of skipping. Fixed in PR #1 and in `66075b` (the identical literal in `tools/build_cases.py`); `TestPathsAreCrossPlatform` now fails on any reintroduction.
- [x] Fresh-venv reproducibility — a second venv built from `requirements.txt` alone: 371 passed (pre-Phase-7-fix run; the current suite is 378)

**The determinism result needed a correction to be honest.** The first version of the test compared
the full serialised response and reported **0.2**. The only differing fields were the five
`QueryMetrics` wall-clock timings — a clock reading is different every time it is taken. Comparing
them measures the clock, not the system. The claim worth making is narrower and now tested: the
answer, claims, retrievals, verifications and summary are byte-identical across five runs. Both
numbers are recorded so the change of method is visible.

**Two harness bugs were found by measurement, not by review**, and both are now regression-tested:
a `ctypes` call whose unset `restype` silently truncated RSS to **0.0 MB** (an implausible-looking
measurement of nothing), and a determinism check that was really a clock check.

**A third and fourth finding: the labelled set caught two real verifier defects.** Comparing one
sentence against a whole 180-word paragraph meant six plainly-supported claims returned
`contradiction_detected` because "not an OCR engine" appeared somewhere in the chunk; and the
negation check compared *cue words* rather than *polarity*, so "does not depend" and "no …
required" read as opposite. Accuracy over the 24 cases moved 0.292 → 0.625 → 0.667. Neither defect
was visible to the unit suite; both are now covered by tests. See
[15 §7.4](15_PROGRESS_TRACKER.md#74-calibration--the-threshold-is-now-a-measurement-not-a-guess).

**One measured result was bad, and it was reported rather than buried.** At the close of Phase 6 the
abstention rate was **0.000** on three deliberately unanswerable questions (R-24). The empty-index
path was implemented and correct; the trigger for *insufficient* evidence did not exist. Hiding it
would have made the gate pass by omission.

**It was fixed in Phase 7.** A query-coverage gate now runs after retrieval and before generation,
with its floor calibrated on 48 hand-labelled questions: correct abstention **0.750** (18/24),
false abstention **0.000** (0/24). A threshold on the existing cosine `relevance_score` was measured
first and **rejected** ? the two classes overlap on it. Details in
[14_RISK_REGISTER.md](14_RISK_REGISTER.md) and
[10_EVALUATION_METRICS.md](10_EVALUATION_METRICS.md).

## 8. Phase 7 — Stage 3 Readiness

**Owner:** All · **Delivers:** the submission package

### Scope

| # | Item |
|---|---|
| 7.1 | Evidence tracker complete: every report claim → real artifact |
| 7.2 | Screenshots captured of **actual** running states (each labelled captured vs schematic) |
| 7.3 | Reproducible logs: install, test, demo, metrics |
| 7.4 | Commit history reviewed per member; contributions verified against actual authorship |
| 7.5 | Stage 3 report drafted from the tracker — never from memory |
| 7.6 | Viva script rehearsed: [11_DEMO_AND_VIVA_PREPARATION.md](11_DEMO_AND_VIVA_PREPARATION.md) |
| 7.7 | Correct Stage 2's citation mis-numbering (I-01) rather than inheriting it |
| 7.8 | Deviations log updated with every Stage 3 decision that differs from Stage 2 |

### Gate G7

**Result: NOT PASSED. Two boxes cannot be ticked, and one is waiting on a person.**

- [x] Every quantitative claim traces to an artifact — the report draft contains no number without a
  row in [12](12_STAGE_3_EVIDENCE_TRACKER.md) and a captured file in [logs/](../logs/README.md)
- [x] No fabricated numbers, screenshots, commits, or rates anywhere — screenshots are **absent and
  labelled absent**, not invented; §13 of the report is empty with the reason stated
- [ ] **Team contributions reflect actual commit authorship — NOT MET.** `git log --author=` has no
  output because this directory is not a repository (**B-05**). Needs `git init` and a human decision
- [ ] **All three members can answer every question in the viva doc unaided — NOT MET.** The script is
  updated and rehearsable ([11](11_DEMO_AND_VIVA_PREPARATION.md) is current as of Phase 7), but nobody
  has actually run it with a person watching. Three R-23 manual UI checks are in the same position
- [x] Deviation notes for the Python pin (ADR-0001) and any Chroma fallback — D-10 amended in
  [01 §3](01_REQUIREMENTS.md#3-stage-2-versus-stage-1-deviations-log), and nine Stage 3 departures
  recorded in [01 §3.1](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log)
- [ ] **Screenshots S1–S9 captured — NOT MET.** Needs someone at a screen. See
  [16 §15](16_STAGE_3_REPORT_DRAFT.md#15-what-this-draft-is-not-yet)

**What Phase 7 did complete:** 7.1 (tracker audited), 7.3 (nine logs captured), 7.5 (report drafted
at [16_STAGE_3_REPORT_DRAFT.md](16_STAGE_3_REPORT_DRAFT.md)), 7.6 (viva script brought current),
7.7 (I-01 checked — the Stage 0 finding **did not reproduce**, so R-04 closes), 7.8 (deviations log
extended to D-19).

**One Phase 7 finding worth recording:** the Phase 0 audit had flagged Stage 2's reference list as
mis-numbered. Checking the extracted text found `Magesh` and `legal research` occur zero times, and a
citation audit found zero dangling and zero orphaned references. The defect was not there. An audit
finding closed by measurement rather than assumed is worth more than one left standing.

## 9. Critical path

```text
Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7
   │           │           │           │
   │           │           │           └── depends on stable pipeline API
   │           │           └── the project's core contribution; most scrutiny
   │           └── retrieval must be measurable before verification means anything
   └── everything depends on trustworthy ingestion + page metadata
```

**Phase 4 is the critical path and the highest-risk phase.** It is where the project's actual
contribution lives, and it is where a rushed implementation produces indefensible verification
semantics. If time must be cut, cut Phase 5 polish and Phase 7 extras — **never** Phase 4 rigour.

## 10. What gets cut, in order, if the deadline bites

1. Phase 5 visual polish beyond the core surfaces
2. Phase 7 extras (extra screenshots, extra metrics)
3. FLAN-T5 abstractive generation (ADR-0011 — already optional)
4. Chroma persistence (keep in-memory + TF-IDF, log honestly)
5. Calibration depth (smaller labelled set, clearly stated as small)

**Never cut:** Phase 2 (ingestion correctness), Phase 4 verification semantics, the offline
deterministic path, the test suite, or the evidence discipline.

## 11. Progress tracking

Update [15_PROGRESS_TRACKER.md](15_PROGRESS_TRACKER.md) at the end of every phase with: phase status,
files changed, real test output, measured numbers, blockers, and the next action. Tick a gate box here
only when its evidence actually exists.
