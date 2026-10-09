# 15 — Progress Tracker

**Status:** Phase 7 in progress - report drafted, awaiting manual items - Last updated 2026-10-08
**Related:** [Roadmap](06_IMPLEMENTATION_ROADMAP.md) · [Evidence Tracker](12_STAGE_3_EVIDENCE_TRACKER.md) · [Risk Register](14_RISK_REGISTER.md) · [Gap Analysis](03_GAP_ANALYSIS.md)

---

## 1. Current status

> ### `PHASE 7 ACTIVE — GATE G7 NOT YET PASSED`

| | |
|---|---|
| **Phase complete** | Phases 0–6: research, documentation, foundation, retrieval, verification, UI, testing + hardening |
| **Phase in progress** | **7** (Stage 3 readiness) — report **drafted** at [16_STAGE_3_REPORT_DRAFT.md](16_STAGE_3_REPORT_DRAFT.md), logs captured in [logs/](../logs/README.md) |
| **G7 blocked on** | **Screenshots S1–S9** (no human at a screen), **B-05** (no repository ⇒ no contribution table, no CI), semantic-profile figures (no weights) |
| **Tests written** | **429** across `test_core.py` (64), `test_retrieval.py` (80), `test_verification.py` (130), `test_ui.py` (98), `test_hardening.py` (57) |
| **Commits made** | **2** — `fd2be70` (Phase 7, attributed) and `9772226` (Phases 0–6, **placeholder author**, B-05) |
| **CI** | **GREEN.** Run [37880879892](https://github.com/Purv-Jain/Aries/actions/runs/37880879892) on `66075b`: `offline (ubuntu-latest)`, `offline (windows-latest)`, `security-sweep` all **success**. B-08 closed |
| **Model weights downloaded** | 0 — semantic and abstractive paths written, **unmeasured** |
| **Calibrated** | `verified_threshold` 0.62 → **0.63**, from a 24-case labelled set; false-`Verified` 0.125 → **0.000** |
| **Metrics measured** | 13 of 24. 4 explicitly **not measured** (model load, semantic-profile figures, FLAN-T5 marker coverage, semantic determinism) |

## 2. Phase status

| Phase | Name | Status | Owner | Gate | Evidence |
|---|---|---|---|---|---|
| 0 | Open-source research + repository audit | **DONE** | All | Research delivered | [02](02_OPEN_SOURCE_RESEARCH.md), [03](03_GAP_ANALYSIS.md) |
| 1 | Documentation-first engineering | **DONE** | All | Docs delivered | This document set |
| 2 | Foundation + PDF processing | **DONE** | Bhavya / Purv | G2 **passed** | 56 tests; see §7 |
| 3 | Retrieval | **DONE** | Purv | G3 **passed** | `pytest -q` → 144 passed; see §7 |
| 4 | Generation + verification | **DONE** | Rishabh / Purv | G4 **passed** | `pytest -q` → 227 passed; see §7 |
| 5 | Premium UI | **DONE** | Purv | G5 **passed**, 3 manual items pending | `pytest -q` → 325 passed; headless HTTP 200; see §7 |
| 6 | Testing + hardening | **DONE** | Bhavya | G6 **passed**, CI green | `pytest -q` → 429 passed; see §7 |
| 7 | Stage 3 readiness | **IN PROGRESS** | All | G7 **not passed** — 4 of 8 scope items done, 3 blocked | [16_STAGE_3_REPORT_DRAFT.md](16_STAGE_3_REPORT_DRAFT.md), [logs/](../logs/README.md) |

## 3. Completed outputs

| # | Output | Path | Notes |
|---|---|---|---|
| 1 | Project README | [README.md](../README.md) | Entry point, stack, ground rules |
| 2 | Agent instructions | [AGENTS.md](../AGENTS.md) | 13 sections; persistent across sessions |
| 3 | Project charter | [00_PROJECT_CHARTER.md](00_PROJECT_CHARTER.md) | Scope, constraints, success criteria |
| 4 | Requirements | [01_REQUIREMENTS.md](01_REQUIREMENTS.md) | 50 FR, 12 NFR, 8 SEC, 17 EC, 10 deviations |
| 5 | Open-source research | [02_OPEN_SOURCE_RESEARCH.md](02_OPEN_SOURCE_RESEARCH.md) | 18 candidates, live API evidence, weighted scoring |
| 6 | Gap analysis | [03_GAP_ANALYSIS.md](03_GAP_ANALYSIS.md) | Workspace audit, 15 gaps, 5 inconsistencies, 10 missing reqs |
| 7 | Architecture | [04_SYSTEM_ARCHITECTURE.md](04_SYSTEM_ARCHITECTURE.md) | 5 Mermaid diagrams, verifier design, injection defence |
| 8 | ADRs | [05_TECH_STACK_AND_ADRS.md](05_TECH_STACK_AND_ADRS.md) | ADR-0001 → ADR-0013 |
| 9 | Roadmap | [06_IMPLEMENTATION_ROADMAP.md](06_IMPLEMENTATION_ROADMAP.md) | 6 phases, gates G2–G7, cut order |
| 10 | UI/UX spec | [07_UI_UX_DESIGN_SPEC.md](07_UI_UX_DESIGN_SPEC.md) | Tokens, layout, 6 surfaces, 17 states, a11y |
| 11 | Data contracts | [08_DATA_MODELS_AND_API_CONTRACTS.md](08_DATA_MODELS_AND_API_CONTRACTS.md) | 20 types, ID scheme, 20 contract tests |
| 12 | Testing strategy | [09_TESTING_STRATEGY.md](09_TESTING_STRATEGY.md) | 17 scenarios, fixtures, security, CI |
| 13 | Evaluation metrics | [10_EVALUATION_METRICS.md](10_EVALUATION_METRICS.md) | 24 metrics, 24-case plan, all `not measured` |
| 14 | Demo + viva | [11_DEMO_AND_VIVA_PREPARATION.md](11_DEMO_AND_VIVA_PREPARATION.md) | 6-beat script, Q&A, traps |
| 15 | Evidence tracker | [12_STAGE_3_EVIDENCE_TRACKER.md](12_STAGE_3_EVIDENCE_TRACKER.md) | All rows `PLANNED` |
| 16 | Team contributions | [13_TEAM_CONTRIBUTIONS.md](13_TEAM_CONTRIBUTIONS.md) | Planned vs. verified, both empty of results |
| 17 | Risk register | [14_RISK_REGISTER.md](14_RISK_REGISTER.md) | 20 risks + 5 accepted |
| 18 | Progress tracker | this file | — |
| 19 | Stage 1 report text (extracted) | [reference/stage1_report_text.md](reference/stage1_report_text.md) | 11 pages, 22,796-byte markdown |
| 20 | Stage 2 report text (extracted) | [reference/stage2_report_text.md](reference/stage2_report_text.md) | 15 pages, 33,654-byte markdown |
| 21 | Pinned dependency set | [requirements.txt](../requirements.txt) | 9 direct pins; all installed into `.venv` on CPython 3.14.6 |
| 22 | Typed data contracts | [src/models.py](../src/models.py) | `DocumentPage`, `EvidenceChunk`, `IndexReport`, `DocumentSummary`, `IngestFailure`, `ChunkConfig`, `ResourceLimits`, `Reason`, ID scheme |
| 23 | PDF ingestion | [src/pdf_ingestion.py](../src/pdf_ingestion.py) | Validation, `pypdf` → `pdfplumber` fallback, scanned detection, sanitisation, injection flagging |
| 24 | Sentence-aware chunking | [src/chunking.py](../src/chunking.py) | Regex splitter (ADR-0003), exact word overlap, no cross-page chunks |
| 25 | Test suite | [tests/test_core.py](../tests/test_core.py) | 64 tests, in-process PDF fixture builder, no binary blobs, no network |
| 26 | Path bootstrap | [conftest.py](../conftest.py) | Makes bare `pytest -q` work, not only `python -m pytest` |
| 27 | Ignore rules | [.gitignore](../.gitignore) | `.venv/`, `.chroma/`, uploads, secrets |
| 28 | Embedding backends | [src/embeddings.py](../src/embeddings.py) | `EmbeddingBackend` protocol, TF-IDF (default), lazy MiniLM with typed degradation |
| 29 | Vector stores | [src/vector_store.py](../src/vector_store.py) | `InMemoryVectorStore` (deterministic), `ChromaVectorStore` (persistent, re-scored, tie-broken) |
| 30 | Orchestration | [src/pipeline.py](../src/pipeline.py) | `index` / `remove_document` / `reindex_document` / `index_stats` / `_retrieve` |
| 31 | Pytest configuration | [pytest.ini](../pytest.ini) | `semantic` marker; default run is offline-only |
| 32 | Shared fixtures | [tests/conftest.py](../tests/conftest.py) | In-process PDF builder, all 10 document fixtures, offline config |
| 33 | Retrieval tests | [tests/test_retrieval.py](../tests/test_retrieval.py) | 80 tests: EC-05, EC-08, EC-14/15, CT-08, FR-16→FR-28, degradation, Chroma persistence |
| 34 | Answer generation | [src/generator.py](../src/generator.py) | Extractive default (offline, injection-proof), optional FLAN-T5 with visible degradation, marker attribution from retrieved data only |
| 35 | Citation verification | [src/verifier.py](../src/verifier.py) | Marker grammar, resolution, containment overlap, `0.7·sim + 0.3·overlap`, numeric + negation + antonym checks, config-driven labels |
| 36 | Verification tests | [tests/test_verification.py](../tests/test_verification.py) | 114 tests: EC-09→EC-13, EC-16, EC-17, CT-09→CT-19, SEC-05 end-to-end |
| 37 | Streamlit UI | [app.py](../app.py) | Dashboard, Library, Workspace; all activity states; namespaced CSS only; no duplicated pipeline logic |
| 38 | UI tests | [tests/test_ui.py](../tests/test_ui.py) + [tests/app_under_test.py](../tests/app_under_test.py) | 98 tests; imports `app.py` directly rather than reimplementing its render path |
| 39 | CLI demo | [run_demo.py](../run_demo.py) | FR-48/49: exit 0/1/2, `--json`, identical output across runs, imports only the public API |
| 40 | Labelled evaluation set | [tests/data/eval_cases.jsonl](../tests/data/eval_cases.jsonl) | 24 cases from the real Stage 2 report; 58% negative or partial; every passage verbatim-checked |
| 41 | Evaluation harness | [tools/evaluate.py](../tools/evaluate.py) + [tools/build_cases.py](../tools/build_cases.py) | Sweeps `verified_threshold`; rebuilds the set from the fixture; results in [eval_results.json](../tests/data/eval_results.json) |
| 42 | Measurement harness | [tools/measure.py](../tools/measure.py) | Latency, Recall@k, MRR, RSS, determinism, abstention → [metrics.json](../tests/data/metrics.json) |
| 43 | Hardening tests | [tests/test_hardening.py](../tests/test_hardening.py) | 46 tests: evaluation integrity, calibration re-run, security sweep, metrics re-run, CLI, CI config |
| 44 | CI workflow | [.github/workflows/tests.yml](../.github/workflows/tests.yml) | Offline matrix on 3.14 plus a separate security sweep. **Green** — run 37880879892 (B-08 closed) |
| 45 | **Stage 3 report draft** | [docs/16_STAGE_3_REPORT_DRAFT.md](16_STAGE_3_REPORT_DRAFT.md) | 15 sections, drafted from the evidence tracker only. **Not submission-ready** — §15 lists what is missing |
| 46 | **Reproducible logs** | [logs/README.md](../logs/README.md) | 9 captured command outputs: environment, test run, demo, metrics, sweep, headless UI, 3 abstention cases |
| 47 | **Stage 3 deviations log** | [docs/01 §3.1](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log) | D-11 → D-19, each forced by a measurement |

## 4. Phase 0 findings — the short version

| # | Finding |
|---|---|
| 1 | **No Stage 2 prototype code exists in this workspace.** Everything is `Planned` again. |
| 2 | Both reference PDFs located at `C:\Users\purvj\Downloads\.pdf\` (different filenames than the brief) and extracted to `docs/reference/`. |
| 3 | Environment: Python **3.14.6** only; `chromadb` **not installed**; most of the Stage 2 stack already present globally. |
| 4 | 18 open-source candidates evaluated with live GitHub/HF/PyPI API evidence. |
| 5 | **Every candidate that shows citations only formats them. None computes per-claim support.** That is the project's justification. |
| 6 | 8 candidates legally unusable (no licence / `NOASSERTION` / GPL-3.0). 1 (`amazon-science/RefChecker`) is archived. |
| 7 | `citation-needed/citation-needed` is a **404** on GitHub; the real project is on Wikimedia GitLab, MIT, dormant, and OpenAI-dependent. |
| 8 | Both required models are **Apache-2.0**. `all-MiniLM-L6-v2` has `max_seq_length = 256` — the empirical basis for the 180-word chunk decision. |
| 9 | Strategy **B** (standalone + libraries) scores **9.00** vs. hybrid 8.00 and the best fork 5.70. |
| 10 | `chromadb` ships a `cp39-abi3` wheel, so it should install on 3.14 — **unverified**. → R-01 |

## 5. Decisions log

| # | Date | Decision | Rationale | Document |
|---|---|---|---|---|
| D-01 | 2026-10-08 | Project root is `C:\Users\purvj\rag-academic-assistant` | No repo existed; home-directory root would pollute the workspace. Chosen by the user. | — |
| D-02 | 2026-10-08 | Strategy B — standalone, reuse libraries not a fork | Weighted scoring; no candidate satisfies the brief | [ADR-0009](05_TECH_STACK_AND_ADRS.md#adr-0009--build-standalone-reuse-libraries-not-a-fork) |
| D-03 | 2026-10-08 | Reference PDFs extracted to `docs/reference/` | Greppable, durable, reviewable; PDFs remain source of truth | [03 §2.2](03_GAP_ANALYSIS.md#22-reference-documents--located) |
| D-04 | 2026-10-08 | Third-party mirror results discarded | `github.laiyagushi.com` mirrors are not authoritative for licence or completeness | [02 §1](02_OPEN_SOURCE_RESEARCH.md#1-method-and-honesty-statement) |
| D-05 | 2026-10-08 | Regex sentence splitter, no NLTK/spaCy | Resolves Stage 2 gap I-02; ~40 testable lines; explainable at viva | [ADR-0003](05_TECH_STACK_AND_ADRS.md#adr-0003--sentence-splitting-without-an-nlp-dependency) |
| D-06 | 2026-10-08 | `token_overlap` = containment, not Jaccard | Claims are short summaries of long passages; Jaccard systematically under-scores correct citations | [04 §5.2](04_SYSTEM_ARCHITECTURE.md#52-what-each-term-is-precisely) |
| D-07 | 2026-10-08 | Added numeric + negation + antonym contradiction checks | High lexical overlap can still mean a contradiction; Stage 2 had no such check | [04 §5.5](04_SYSTEM_ARCHITECTURE.md#55-contradiction-check) |
| D-08 | 2026-10-08 | Added prompt-injection controls (SEC-05) | PDF text is untrusted; Stage 2 never addressed it | [04 §7](04_SYSTEM_ARCHITECTURE.md#7-untrusted-content-and-prompt-injection) |
| D-09 | 2026-10-08 | No citation re-attribution in the MVP | Silently moving a citation destroys the traceability guarantee | [ADR-0008](05_TECH_STACK_AND_ADRS.md#adr-0008--no-citation-re-attribution-in-the-mvp) |
| D-10 | 2026-10-08 | Stage 2 claims treated as unverified historical report claims | Not reproducible here; ADR-0013 | [03](03_GAP_ANALYSIS.md) |
| D-11 | 2026-10-08 | **Python pinned to CPython 3.14.6** (Option A) | Human decision, Phase 2. Logged deviation from Stage 2's 3.13.5, and a superset of its actual 3.10+ constraint | [ADR-0001](05_TECH_STACK_AND_ADRS.md#adr-0001--pin-the-python-version) |
| D-12 | 2026-10-08 | `chromadb` install + persistence smoke test moved **into Phase 2**, ahead of roadmap item 3.10 | Knowing the answer before designing against it retires R-01 cheaply; the roadmap itself treated ADR-0001 as a Phase 2 gate item | [06 §3](06_IMPLEMENTATION_ROADMAP.md#gate-g2), [R-01](14_RISK_REGISTER.md) |
| D-13 | 2026-10-08 | Identity helpers (`compute_source_id`, `compute_chunk_id`) live in `src/models.py` | An ID scheme implemented twice eventually disagrees with itself; a wrong ID is a citation that points nowhere | [08 §4](08_DATA_MODELS_AND_API_CONTRACTS.md#4-identity-and-id-scheme) |
| D-14 | 2026-10-08 | `char_count` / `word_count` are `field(init=False)`, computed in `__post_init__` | A caller must not be able to construct a page whose `char_count` disagrees with its `text` | [08 §2.1](08_DATA_MODELS_AND_API_CONTRACTS.md#21-documentpage) |
| D-15 | 2026-10-08 | Root `conftest.py` added | Bare `pytest -q` (what CI runs) failed without it; only `python -m pytest` happened to work | [09 §7](09_TESTING_STRATEGY.md#7-ci) |
| D-16 | 2026-10-08 | **Retrieval is `pipeline._retrieve`, not `ask()`** | `ask()` returns an `AnswerResponse` containing a `GeneratedAnswer` and verifications — types that arrive in Phase 4. Exposing it now would mean inventing a half-built answer contract. `PipelineConfig` therefore has no `verification` or `generator` field yet; EC-05 and the empty-index guard are implemented and tested at the layer `ask()` will delegate to, so neither is written twice | [08 §10.3](08_DATA_MODELS_AND_API_CONTRACTS.md#103-public-api) |
| D-17 | 2026-10-08 | `RetrievalResult.backend` records the **embedding** backend, not the store | "0.72 from TF-IDF" is a meaningful claim; "0.72 from memory" says nothing about how the number was produced. `set_similarity(fn, name)` passes the scorer's identity into the store | [08 §7.1](08_DATA_MODELS_AND_API_CONTRACTS.md#71-retrievalresult) |
| D-18 | 2026-10-08 | Mid-session degradation marks already-embedded chunks `stale_chunks` | A TF-IDF query cannot meaningfully score MiniLM vectors. Rebuilding the whole index mid-upload would be correct but would take far longer than the user asked for, so the count is reported instead | [04 §6](04_SYSTEM_ARCHITECTURE.md#6-failure-modes-and-degradation) |
| D-19 | 2026-10-08 | Persisted TF-IDF index is made queryable by **refitting the vocabulary** from stored chunk texts on startup | A TF-IDF vector is only comparable to one built from the same vocabulary, and the vocabulary lived only in memory — so a restarted process could not query its own index (EC-15). This is a deterministic lexical refit, not re-embedding; no model is involved | [ADR-0005](05_TECH_STACK_AND_ADRS.md#adr-0005--two-profiles-one-pipeline) |
| D-20 | 2026-10-08 | Chroma: `hnsw:search_ef = 256` and 4× candidate over-fetch, then re-rank with our own tie-break | Chroma's HNSW is approximate and its tie order is arbitrary. Without both, the two stores returned different orderings for identical scores. Exactness at large scale is **not** claimed — [04 §8](04_SYSTEM_ARCHITECTURE.md#8-determinism) says so | [08 §7](08_DATA_MODELS_AND_API_CONTRACTS.md#7-retrieval-contract) |
| D-21 | 2026-10-08 | `ask()` is now public; `_retrieve` stays private | The public API in [08 §10.3](08_DATA_MODELS_AND_API_CONTRACTS.md#103-public-api) is complete. `ask()` is the *only* way the UI reaches retrieval — one entry point is what makes FR-47 structurally true rather than a review convention | [08 §10.3](08_DATA_MODELS_AND_API_CONTRACTS.md#103-public-api) |
| D-22 | 2026-10-08 | `rescale_cosine_to_unit_interval` is decided by the **backend**, not by the config file | TF-IDF cosine is already `[0,1]`; rescaling it maps an unrelated claim from 0.0 to 0.5, so the system would look *more confident the less the evidence supported it*. The flag describes a property of the similarity function, and only the backend knows it | [04 §5.2](04_SYSTEM_ARCHITECTURE.md#52-what-each-term-is-precisely) |
| D-23 | 2026-10-08 | Generator markers carry **no page** when the page is unknown, and the verifier re-resolves from `raw` alone | A generator vouching for its own citation is exactly what the verifier exists to check. Resolution is therefore never taken on the generator's authority — including its `resolved` flag | [ADR-0008](05_TECH_STACK_AND_ADRS.md#adr-0008--no-citation-re-attribution-in-the-mvp) |
| D-24 | 2026-10-08 | `page_mismatch` separated from `unresolvable_reference` | One tells the user the citation is fictional; the other that it names a real paper at the wrong page. Different problems deserve different words and different UI states | [08 §6.2](08_DATA_MODELS_AND_API_CONTRACTS.md#62-verification) |
| D-25 | 2026-10-08 | `_negations()` reads raw tokens, **not** `content_tokens()` | `not` is a stopword. Routing negation through the token filter that removes low-value words would delete the entire contradiction signal — and the code would still run, producing plausible numbers, and be silently wrong | [04 §5.5](04_SYSTEM_ARCHITECTURE.md#55-contradiction-check) |
| D-26 | 2026-10-08 | EC-11's fixture is a **lexical** paraphrase; the synonym-substitution case is recorded as a limit | A true synonym paraphrase scores 0.10 containment and is `Unsupported`. Using it as the test would have required loosening the threshold to make a test pass — the wrong direction. The limit is documented and is honest report material | [09 §4.1](09_TESTING_STRATEGY.md#4-the-17-mandated-scenarios) |

## 6. Blockers

| # | Blocker | Blocks | Needs | Owner |
|---|---|---|---|---|
| ~~B-01~~ | ~~Phase 2 not approved~~ | — | **RESOLVED** — approved 2026-10-08 | — |
| ~~B-02~~ | ~~Python version undecided~~ | — | **RESOLVED** — pinned 3.14.6, ADR-0001 accepted | — |
| ~~B-03~~ | ~~`chromadb` not installed~~ | — | **RESOLVED** — installed 1.5.9, persists and reloads on 3.14.6 | — |
| ~~B-04~~ | ~~Phase 2 fixtures not built~~ | — | **RESOLVED** — generated in-process by `tests/conftest.py::build_pdf` | — |
| **B-05** | **The Phase 0-6 commit carries a placeholder author** | Per-member contribution table (report §13, item 7.4) | **PARTLY RESOLVED, disclosure chosen over rewriting history.** A repository now exists at [Purv-Jain/Aries](https://github.com/Purv-Jain/Aries) with two commits. `9772226` (all of Phases 0-6) was authored by the git default placeholder `Your Name <your.email@example.com>`, because the repo was created before the identity was configured; `fd2be70` (Phase 7) is correctly attributed to `Purv-Jain <purv.jain24@sakec.ac.in>`. The placeholder commit **cannot be decomposed** into three contributions, so no per-member split is derivable. Rewriting it was considered and **rejected**: it changes a commit on a public remote, invalidates it for anyone who cloned, and needs both teammates to coordinate. Correct it after submission. | Human |
| **B-06** | ~~No real academic PDF in the repo~~ | R-11 | **RESOLVED for measurement** — the team's own Stage 2 report (15 pages) was used as the fixture. See **B-07** for the remaining issue | — |
| **B-07** | **The fixture PDF lives in `~/Downloads/.pdf/`, outside the project** | Reproducing the calibration on a fresh clone | A decision: commit the report under `tests/data/`, or document that `tools/evaluate.py` requires a local copy | Human |
| ~~B-08~~ | ~~`ubuntu-latest` CI job fails~~ | Gate G6 item | **RESOLVED AND VERIFIED 2026-10-09.** Cause: `PROJECT_ROOT / r"tests\data\eval_cases.jsonl"` resolves to a *single filename* on POSIX, where a backslash is a legal filename character. The nine `TestEvaluationSetIntegrity` tests called `_load_cases()` with no skip guard, so they raised `FileNotFoundError` instead of skipping — which is why the job failed rather than silently under-reporting. Fixed in PR #1 and in `66075b` (the identical literal in `tools/build_cases.py`). **Verified green**: run [37880879892](https://github.com/Purv-Jain/Aries/actions/runs/37880879892) on `66075b`, all three jobs `success`. `TestPathsAreCrossPlatform` fails on any reintroduction | — |

**B-05 is partly resolved** — the repository exists and Phase 7 is correctly attributed; the
Phase 0–6 commit keeps its placeholder author by deliberate decision. **B-08 is resolved and verified green** — the ubuntu failure was a Windows path literal that made the
evaluation tests raise `FileNotFoundError`, found and fixed via PR #1. Run 37880879892 is green on all three jobs.

Remaining blockers and what each needs:

| # | Needs |
|---|---|
| **B-05** | Post-submission history rewrite, or leave it — disclosure is already in report §13 |
| **B-07** | A decision on whether the fixture PDF may be committed |
| **B-08** | Nothing — resolved. Re-run CI to confirm green |

Nothing is blocked on external parties, network access, or funding. Everything outstanding needs
either a decision or a pair of hands.

## 7. Test results

Suite totals, phase by phase. Zero failures across every run; no test was skipped or weakened to
reach a green result.

| Date | Phase | Command | Profile | Result |
|---|---|---|---|---|
| 2026-10-08 | 2 | `pytest -q` | Offline | 56 passed in 0.82s |
| 2026-10-08 | 2 | `python -m pytest -q` | Offline | 56 passed in 1.12s |
| 2026-10-08 | 2 | as above, `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` | Offline | 56 passed in 0.66s |
| 2026-10-08 | 3 | `pytest -q` | Offline | 144 passed, 4 deselected in 16.92s |
| 2026-10-08 | 3 | as above + `HF_DATASETS_OFFLINE=1` | Offline | 144 passed, 4 deselected in 15.99s |
| 2026-10-08 | 3 | as above, repeated (`-p no:randomly`) | Offline | 144 passed, 4 deselected in 14.47s |
| 2026-10-08 | 4 | `pytest -q` | Offline | 227 passed, 6 deselected in 12.22s |
| 2026-10-08 | 4 | as above, hub disabled | Offline | 227 passed, 6 deselected in 10.99s |
| 2026-10-08 | 5 | `app.py` written ? three surfaces, all activity states, namespaced CSS design system; `reconfigure()` and `last_report` added to the pipeline; `tests/test_ui.py` (98 tests) + `tests/app_under_test.py` shim; **325 passed, 6 deselected**; gate G5 passed with 3 manual items pending; 13 contrast ratios measured |
| 2026-10-08 | 6 | `run_demo.py` (FR-48/49); `tools/build_cases.py` + `tools/evaluate.py` ? **24-case hand-labelled set**, every passage verbatim-checked; `tools/measure.py` ? 13 metrics on the real 15-page report; `tests/test_hardening.py` (46 tests); `.github/workflows/tests.yml`; **405 passed, 6 deselected**; gate G6 passed except CI (B-05). `verified_threshold` 0.62 ? **0.63**; false-`Verified` 0.125 ? **0.000**. Two verifier defects found by the evaluation and fixed |
| 2026-10-08 | 6 | `run_demo.py` (FR-48/49); `tools/build_cases.py` + `tools/evaluate.py` -> **24-case hand-labelled set**, every passage verbatim-checked; `tools/measure.py` -> 13 metrics on the real 15-page report; `tests/test_hardening.py` (46 tests); `.github/workflows/tests.yml`; **405 passed, 6 deselected**; gate G6 passed except CI (B-05). `verified_threshold` 0.62 -> **0.63**; false-`Verified` 0.125 -> **0.000**. Two verifier defects found by the evaluation and fixed |
| 2026-10-08 | 6 | `run_demo.py` (FR-48/49); `tools/build_cases.py` + `tools/evaluate.py` -> **24-case hand-labelled set**, every passage verbatim-checked against the extraction; `tools/measure.py` -> 13 metrics on the real 15-page report; `tests/test_hardening.py` (46 tests); `.github/workflows/tests.yml`; **405 passed, 6 deselected**; gate G6 passed except CI, which cannot run (B-05). `verified_threshold` 0.62 -> **0.63**; false-`Verified` 0.125 -> **0.000**. Two verifier defects found by the evaluation and fixed |
| 2026-10-08 | 5 | as above, hub disabled | Offline | 325 passed, 6 deselected in 20.85s |
| **2026-10-08** | **6** | **`pytest -q`** | **Offline** | **371 passed, 6 deselected in 64.30s** |
| **2026-10-08** | **6** | **`pytest -q -m "not semantic"`, all three `*_OFFLINE=1`** | **Offline** | **371 passed, 6 deselected in 57.08s** |
| **2026-10-08** | **6** | **fresh venv from `requirements.txt`, then the same command** | **Offline** | **371 passed, 6 deselected in 79.37s** |
| **2026-10-08** | **7** | **`pytest -q`, after 4 verifier fixes (§7.4)** | **Offline** | **402 passed, 6 deselected in 53.50s** |
| — | all | `pytest -q -m semantic` | Semantic | **never run. No MiniLM or FLAN-T5 weights on this machine. Unmeasured, not passed.** |

The **6 deselected** tests carry the `semantic` marker
([09 §6](09_TESTING_STRATEGY.md#6-profile-strategy)). They are written and collectable — pytest
confirming it found them is what `6 deselected` means — but no result exists for them, and no document
in this repository may claim otherwise.

One third-party warning appears in every run and is not ours:
`chromadb/telemetry/opentelemetry/__init__.py:128: DeprecationWarning: 'asyncio.iscoroutinefunction'
is deprecated`. It originates inside `chromadb` on Python 3.14, is harmless, and is left visible
rather than filtered — a suppressed warning hides the next real one too.

> Stage 2 reported "10/10 passing tests" against a prior local prototype not present in this
> workspace ([ADR-0013](05_TECH_STACK_AND_ADRS.md#adr-0013--treat-stage-2-prototype-claims-as-unverified)).
> That is a historical report claim. The current number is **429**, and it is 429 because these are
> this project's own tests.

---

## 7.1 Phase 2–3 coverage

| Case | Covered by | State |
|---|---|---|
| EC-01 wrong file type | `test_ec01_wrong_file_type_is_rejected` | covered |
| EC-02 zero-byte PDF | `test_ec02_zero_byte_pdf_is_rejected` | covered |
| EC-03 encrypted PDF | `test_ec03_encrypted_pdf_is_rejected` | covered |
| EC-04 scanned PDF | `test_ec04_scanned_pdf_states_the_ocr_limitation` | covered |
| EC-05 blank question | `test_ec05_blank_question_is_refused_before_any_search` | covered — the store is replaced by a raiser, so "before any search" is proven rather than inferred |
| EC-06 zero chunks | `test_ec06_...` + `test_ec21_empty_index_is_refused_with_an_actionable_message` | covered — chunking half and store half both |
| EC-07 `overlap >= chunk_size` | `test_chunk_config_rejects_overlap_equal_to_size` | covered |
| EC-08 `top_k` > collection | `test_fr25_...`, `test_top_k_is_clamped_...`, `test_ir4_...` | covered at k = 1, 3, 10, 50 |
| EC-14 multi-document IDs | `TestMultiDocument` (3) + `test_ec14_each_document_keeps_its_own_page_numbers` | covered for identity and pages; citation mapping is Phase 4 |
| EC-15 repeat index + persistence | 4 tests incl. `test_restart_does_not_re_read_the_pdf` | covered — the restart test booby-traps the PDF reader |
| FR-16 one protocol, two backends | `test_both_backends_satisfy_the_protocol` | covered |
| FR-17 MiniLM 384-dim | `TestSemanticProfile` | **written, unmeasured** |
| FR-18 TF-IDF offline | whole suite with the hub disabled | covered |
| FR-19 Chroma persistence | `test_chroma_index_survives_a_new_pipeline_instance` | covered |
| FR-20 deterministic in-memory store | `test_ir3_ties_break_on_chunk_id_...` | covered |
| FR-21 no index from zero chunks | `test_ec21_...` | covered |
| FR-22 remove / re-index | `TestRemovalAndReindex` (7 tests, both stores) | covered |
| FR-23 → FR-28 | `TestPipelineRetrieval` | covered |
| CT-08 no `support_score` on `RetrievalResult` | `test_ct08_...` | covered — asserts absence three ways |
| CT-18 blank query raises | `test_ec05_...` | covered |
| SEC-01 → SEC-04 | `TestContracts`, `TestScannedAndLimits` | covered |
| SEC-05 injection flagging | `test_sec05_...` (Phase 2 half) | covered |

---

## 7.2 Phase 4 coverage

| Case | Covered by | State |
|---|---|---|
| EC-09 valid citation mapping | `test_ec09_valid_marker_resolves_to_the_right_file_and_page` | covered |
| EC-10 fabricated marker | `test_ec10_..._never_repaired` + `..._not_silently_pointed_at_a_real_passage` | covered — the second proves no repair even when a supporting passage exists |
| EC-11 supported paraphrase | `test_ec11_...` + a fixture guard | covered, with the lexical limit recorded (D-26) |
| EC-12 contradictory claim | `test_ec12_contradictory_claim_is_caught_despite_high_overlap` | covered — asserts overlap > 0.5 *and* that the label is not `Verified` |
| EC-13 missing model dependency | `test_ec13_missing_dependency_degrades_and_still_answers` + 4 | covered |
| EC-16 insufficient evidence | `TestAbstention` (7) | covered — an empty index returns an abstained response, not an exception |
| EC-17 offline, no API key | `test_ec17_two_offline_runs_are_byte_identical` | covered — two runs compared string-for-string |
| SEC-05 injection, end to end | `TestPromptInjectionDefence` (5) | covered |
| CT-09 → CT-14, CT-19 | `TestSupportScoreContract`, `TestCitationVerification` | covered |
| FR-29 → FR-40 | `TestExtractiveGenerator`, `TestFlanT5Degradation`, `TestSupportScoreContract` | covered |

---

## 7.3 Phase 5 and 6 verification

| Requirement | How it is checked | Result |
|---|---|---|
| FR-41 dashboard, live stats | `test_dashboard_renders_real_counts_when_indexed` | pass — 1 document, 5 pages, from `index_stats()` |
| FR-42 library, real rows | `test_library_renders_rows_and_real_failures` | pass — a scanned PDF appears with its real reason |
| FR-43 workspace with markers | `test_workspace_renders_an_answer_with_all_three_panels` | pass |
| FR-44 evidence inspector | `test_inspector_shows_both_scores_separately_labelled` | pass — "support score" and "retrieval relevance to your question" are distinct rows |
| FR-45 colour + label + symbol | `test_chip_renders_icon_colour_and_text_together` | pass |
| FR-46 all activity/error states | `test_recovery_guidance_exists_for_every_ingest_reason` | pass — all 10 reason codes |
| FR-47 no duplicated logic | CT-20 AST audit, plus `test_run_demo_does_not_import_leaf_modules` | pass — `app.py` and `run_demo.py` both |
| NFR-10 accessibility | `TestContrast` (13 pairs), focus, reduced-motion, keyboard markers | pass, ratios in §7.3.1 |
| UI-1 headless start | subprocess + HTTP + health check + log scan | pass — 200, no traceback |
| UI-2 no placeholders | AST grep over code only | pass |
| FR-48 CLI demo | `TestRunDemoContract` (7 tests) | pass — exit codes 0/1/2 all exercised |
| FR-49 same input, same output | `test_two_runs_write_identical_json` | pass |

### 7.3.1 Measured contrast ratios (WCAG)

Computed from the palette in [07 §2.1](07_UI_UX_DESIGN_SPEC.md#21-colour). **Measured**, not assumed.

| Pair | Ratio | Target |
|---|---|---|
| body text `#1A1D1A` on canvas `#FBFAF6` | 16.3:1 | AA |
| body text on surface `#FFFFFF` | 17.0:1 | AA |
| secondary `#5A615A` on surface | 6.4:1 | AA |
| secondary on canvas | 6.1:1 | AA |
| primary `#1F4D3D` on canvas | 9.2:1 | AA |
| primary on surface | 9.6:1 | AA |
| primary on muted chip `#E8F0EA` | 8.3:1 | AA |
| **Verified** `#2F6B4F` on `#E7F1EA` | 5.4:1 | AA |
| **Needs Review** `#8A6212` on `#FBF2DF` | 4.9:1 | AA |
| **Unsupported** `#9B2C2C` on `#FAEAEA` | 6.5:1 | AA |
| info `#2F5D8A` on `#EAF1F8` | 6.0:1 | AA |
| evidence passage on sunken `#F4F3EC` | 15.3:1 | AA |
| placeholder `#8A908A` on surface | 3.3:1 | 3:1 large-text floor |

The placeholder pair is the only one below 4.5:1, and it is a non-essential hint on an input the user
has already filled in. Named here rather than quietly counted as AA.

### 7.3.2 Three checks still need eyes on a screen

| Check | State |
|---|---|
| UI-4 greyscale readability (R-23) | **not done** — Phase 7 |
| UI-5 keyboard-only walkthrough (R-23) | **not done** — Phase 7 |
| UI-3 1280 px / 768 px layout (R-23) | **not done** — Phase 7 |

The 98 UI tests prove the render path executes and emits the right content. They cannot see a
layout. Calling the UI visually verified on that basis would be the same overclaim the rest of this
project refuses to make.

### 7.3.3 Phase 6 environment, network and security evidence

**Fresh-venv reproducibility (NFR-05).** A second environment, from `requirements.txt` and nothing
else:

```text
$ python -m venv venv_check
$ venv_check\Scripts\python.exe -m pip install -r requirements.txt      → exit 0
$ venv_check\Scripts\python.exe -m pip list --format=freeze
    chromadb==1.5.9   pdfplumber==0.11.10   pypdf==6.19.0   pytest==9.1.1
    scikit-learn==1.9.0   sentence-transformers==5.7.0   streamlit==1.65.0
    torch==2.13.0     transformers==5.14.1
$ venv_check\Scripts\python.exe -m pytest -q -m "not semantic"
    371 passed, 6 deselected, 1 warning in 79.37s
```

Every pin resolved to the version the project was developed against. One command; no manual steps.

**Network genuinely disabled.** Not asserted from environment variables — a test replaces
`socket.connect` and `socket.create_connection` with a function that **raises**, then runs a full
index → ask → verify cycle: `indexed 46 claims 3`, exit 0. The offline path cannot touch the network
because it is not permitted to try.

**Security sweep — 46 hardening tests.**

| Check | Result |
|---|---|
| No `eval`/`exec`/`compile`/`__import__` in `src/`, `app.py`, `run_demo.py`, `tools/` | pass |
| No `shell=True`; the single `subprocess` use (`wmic`, for CPU/RAM) passes a list | pass |
| No secrets, keys or `.env` anywhere in the tree | pass |
| No hardcoded absolute or user-specific paths in `src/` | pass |
| No network call on the default path | pass |
| No `torch.cuda` reference in `src/` | pass |
| No file opened in a write mode anywhere in `src/` | pass |
| `requirements.txt` fully pinned, no editable / git / index-url entries | pass |

Three of these checks were **wrong on their first run** and were corrected rather than weakened:
`compile` matched `re.compile`, `open(` matched `pdfplumber.open` (which *reads*, as the module's job
requires), and one `subprocess` assertion contradicted its own neighbouring line. Each now has a
`not_vacuous` companion proving the check still fires on a real violation — a security test that can
never fail is worse than no test.

---

## 7.4 Calibration — the threshold is now a measurement, not a guess

`tools/build_cases.py` builds a 24-case hand-labelled set from the real Stage 2 report;
`tools/evaluate.py` scores it and sweeps the threshold. Both are re-runnable, and a test re-runs the
evaluation and asserts the stored numbers still hold.

### The labelling set

| Category | Count | Meaning |
|---|---|---|
| supported_direct | 6 | the passage states the claim |
| supported_paraphrase | 4 | same meaning, different wording |
| partial_support | 4 | related, but a number or scope differs |
| unsupported_absent | 3 | on-topic, does not contain the claim |
| contradicted | 3 | the passage states the opposite |
| unresolvable_reference | 2 | the marker names a source never retrieved |
| uncited_claim | 2 | the claim carries no marker |
| **Total** | **24** | **14 of 24 negative or partial — 58%**, satisfying creation rule 2 |

Integrity properties, asserted in `tests/test_hardening.py` rather than claimed:

- **Every passage is verbatim from the extraction.** This caught three cases declaring page 2 while
  the passage was on page 3, and two typed from memory with paraphrased punctuation. Without the
  check, every number below would have been measured against text that does not exist.
- **No case carries an expected system label.** A test rejects any `expected` / `system_label` key,
  so the threshold cannot have been fitted to a target rather than to data.
- **Contradicted cases keep the vocabulary and flip the meaning** — each shares ≥4 content words
  with its passage, so they exercise the contradiction path rather than low similarity.
- **Inter-annotator agreement 23/24 = 0.958.** The single disagreement (`eval_13`) is recorded with
  its reconciliation, per creation rule 6.

### The sweep

`verified_threshold` swept 0.30 → 0.90; `review_threshold` held at half so the bands stay ordered.
Only points where the metrics changed:

| verified | P(Verified) | R(Verified) | F1 | false-`Verified` | accuracy |
|---|---|---|---|---|---|
| 0.30 | 0.643 | 0.900 | 0.750 | **0.357** | 0.667 |
| 0.36 | 0.692 | 0.900 | 0.783 | 0.308 | 0.708 |
| 0.57 | 0.800 | 0.800 | 0.800 | 0.200 | 0.667 |
| 0.59 | 0.889 | 0.800 | 0.842 | 0.111 | 0.708 |
| **0.63** | **1.000** | **0.800** | **0.889** | **0.000** | **0.708** |
| 0.70 | 1.000 | 0.700 | 0.824 | 0.000 | 0.667 |
| 0.80 | 1.000 | 0.400 | 0.571 | 0.000 | 0.500 |
| 0.85 | 1.000 | 0.100 | 0.182 | 0.000 | 0.375 |
| 0.87 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 |

**Chosen: `verified_threshold = 0.63`** — the highest-F1 point with false-`Verified` = 0, the
correctness-first criterion in
[ADR-0007](05_TECH_STACK_AND_ADRS.md#adr-0007--verifier-scope-precision-first-abstention).

It was **0.62** before: an unmeasured guess inherited from Stage 2, where the measured
false-`Verified` rate is **0.125** — one contradicted claim among eight labelled `Verified`. Moving
to 0.63 puts that case, scoring exactly 0.630, above the line.

### What the calibration does *not* establish

24 self-authored cases from one 15-page report, labelled by the people who wrote the system. This
justifies the operating point; it does not prove the threshold is correct in general. R-10 stands, and
the report must say "justified on 24 cases" rather than "validated".

### Five real defects, three of them found by testing the tests

The first two were invisible to the unit suite and surfaced only by running the system against real
academic text. The next three were found in Phase 7 by writing direct unit tests for helper functions
that had only ever been reached indirectly ? the evaluation could not find them, and it should have,
which is worth stating plainly.

1. **The negation check compared one sentence against a whole paragraph.** Six plainly-supported
   claims returned `contradiction_detected` because the 180-word chunk contained "not an OCR engine"
   somewhere while the claim itself had no negation. Now restricted to the passage's best-matching
   sentence.
2. **The negation check compared cue words instead of polarity.** "does not depend" and "no ?
   required" are the same polarity; treating them as a mismatch flagged a correct paraphrase. Now
   compares presence-of-negation, not which word was used.
3. **`_antonym_conflict` searched the wrong token set** (`verifier.py`). It looped over
   `claim_tokens & chunk_tokens`, but a contradiction means the claim uses one member of a pair and
   the passage the other ? so the token under test is never in the intersection. The function fired
   only when the passage happened to contain *both* members, which is the opposite of the
   disagreement it was looking for. **The antonym branch was effectively dead.** Now iterates the
   claim's own tokens.
4. **`_claim_is_negated` could not see the cues it needed.** It intersected a token set built by
   `content_tokens`, which drops stopwords ? and `not`, `no`, `nor` and `without` are all stopwords.
   Four of the ten negation cues were therefore invisible, including the commonest one in English.
   The module's own docstring warns at length against routing negation through `content_tokens`, and
   this path did exactly that. Now reads the raw claim text.
5. **The antonym list paired inflections individually.** `("increase","decrease")`,
   `("increased","decreased")` and `("increases","decreases")` were three separate pairs, so a claim
   saying "increased" and a passage saying "decreased" never met. Now grouped by concept, with seven
   named oppositions ? declaring every pair would have been worse, because through polysemy it makes
   `increased` and `cost` antonyms and "The cost increased" self-contradictory. The check also now
   declines when the passage uses the claim's own direction, so a mixed result is not read as a denial.

Accuracy over the 24 cases: **0.292 ? 0.625 ? 0.667** for the first two, and **unchanged at 0.667**
after the next three. That is the finding worth stating: all five defects were real, and fixing them
moved no measured number, because on this fixture every contradiction the evaluation credits to the
verifier is caught by the numeric and polarity branches. The antonym branch is now correct code that
this labelled set does not exercise.

**The threshold did not move.** Re-running the sweep after the fixes returns the same chosen point:
`verified_threshold = 0.63`, F1 0.889, precision 1.000, recall 0.800, false-`Verified` 0.000
([logs/05_evaluate.txt](../logs/05_evaluate.txt)). Calibration was not invalidated, so no
re-calibration was performed and none is claimed.

All five fixes live in [src/verifier.py](../src/verifier.py). Defects 3?5 are pinned by 31 direct
tests, four of which treat the concept list as data ? every form a matchable token, no form in two
concepts, every concept in an opposition, no dangling reference ? plus 24 parametrised cases covering
detection across inflections, polysemy, mixed results and the negation guard. One test,
`test_the_guard_would_be_dead_if_it_read_filtered_tokens`, asserts the exact failure mode as an
executable claim rather than leaving it in a comment.
---

## 7.5 Abstention — R-24 found, measured, and fixed

**Phase 7, 2026-10-09.** This is the one open risk that was closed rather than documented.

### What was wrong

`pipeline.ask()` had one abstention trigger: the index was empty. With a non-empty index, retrieval
always returned `top_k` passages and the extractive generator always found *something* to quote,
because its sentence scorer has no floor. The verifier was then asked to check claims built from
passages that had nothing to do with the question.

Audited before any change: **8 of 8 out-of-corpus questions answered, 15 claims labelled `Verified`.**

### What was rejected first

A floor on the existing `relevance_score`. Measured on the labelled set:

| floor | correct abstention | false abstention |
|---|---|---|
| 0.12 | 0.30 | 0.00 |
| 0.18 | 0.80 | **0.62** |
| 0.20 | 1.00 | **0.75** |

The two classes overlap on cosine (answerable 0.138–0.257, unanswerable 0.072–0.192). There is no
clean cut, and it was not shipped.

### What was built

`src/pipeline.py:query_coverage` — the fraction of the question's content words present in the
retrieved passages — gated in `ask()` **after retrieval, before generation**, with the floor in
`AbstentionConfig.min_query_coverage` ([ADR-0014](05_TECH_STACK_AND_ADRS.md#adr-0014--refuse-before-generating-on-query-coverage-rather-than-a-relevance-floor)).
The refusal names the unmatched terms; the retrieved passages are still returned so the user can
check it.

Labelled set: [tests/data/abstention_cases.jsonl](../tests/data/abstention_cases.jsonl) — 24
answerable (each naming the page that answers it, 12 distinct pages) and 24 unanswerable, of which
**6 are adversarial**. Authored by reading the report, not by watching retrieval.

### Measured, on the same 15-page report

| Metric | Before | After |
|---|---|---|
| Correct abstention (24 unanswerable) | **0.000** | **0.750** (18/24) |
|  clear out-of-domain negatives | 0.000 | **1.000** (18/18) |
|  adversarial negatives | 0.000 | **0.000** (0/6) |
| False abstention (24 answerable) | 0.000 | **0.000** (0/24) |
| False-`Verified` on the original 10 questions | **15** | **0** |
| Claims emitted on those 10 questions | 50 | **0** |
| Claims on the 8 answerable questions (gate off vs on) | 40 | 40 — **unchanged** |

### Threshold choice, including the one that scored better

Floor **0.50**. The sweep gives 0.65 a *higher* correct-abstention rate (0.792) at the same 0.000
false-abstention rate, so it dominates 0.50 on the table. **Rejected anyway:** its margin to the
nearest answerable case is 0.017 against 0.167 at 0.50. Choosing it would be fitting the threshold to
the dataset that justifies it. Full table in
[10 §4b](10_EVALUATION_METRICS.md#4b-abstention-calibration--the-sweep-behind-min_query_coverage).

### What is still open

The 6 adversarial cases. Coverage cannot tell "the words are here" from "the answer is here", and
their claims still reach `Verified`. They are locked into the labelled set by
`test_the_adversarial_misses_are_recorded_rather_than_hidden`, which **fails if the rate ever
reaches 1.000** so an improvement cannot pass unnoticed. Closing the gap needs entailment (P3), not a
better threshold.

### Also fixed along the way

`GeneratedAnswer.notes` accepted a bare `str` where a tuple was declared. `notes=( "a" "b" )` is a
string, so it iterated character by character and rendered as single letters in the UI. Now coerced
in `__post_init__`, and the cause is recorded in [08 §7.3](08_DATA_MODELS_AND_API_CONTRACTS.md).

**Tests added: 24** — 16 in `test_verification.py` (gate behaviour, the refusal text, the
pre-generation ordering, the no-content-terms decision, determinism, and the coverage signal in
isolation) and 8 in `test_hardening.py` (set quality, and four assertions locking the measured rates
against the real fixture). No existing test was weakened, skipped or deleted.

## 8. Measurements taken

### 8.1 Phase 6 — on the real Stage 2 report

Fixture: `FAI_PE_Microproject_Stage_2_Report_Revised.pdf` — **15 pages, 46 chunks**. Two-column
academic prose with tables: the hardest input the project will face. **R-11 is closed by
measurement.** Environment: Windows 11 build 26300, Intel64 Family 6 Model 154, 8 logical CPUs,
CPython 3.14.6, no GPU. Full output: [tests/data/metrics.json](../tests/data/metrics.json).

| Metric | Value | Method |
|---|---|---|
| **Recall@1** | **0.667** (6/9) | 9 hand-authored questions, one relevant page each |
| **Recall@3 / @5 / @10** | **1.000** | same |
| **MRR** | **0.778** | mean reciprocal rank of the relevant page |
| Marker coverage (extractive) | **1.000** | every claim carried a resolvable marker |
| Citation resolution rate | **1.000** | no `unresolvable_reference` |
| Indexing latency | **3.236 s per 100 pages** | 3 runs, fresh pipeline each; median 0.486 s for 15 pages |
| Query latency p50 / p95 | **12.40 / 15.55 ms** | 27 queries after warm-up, offline profile |
| Peak RSS | **191.3 MB** (baseline 190.0 MB) | sampled after each stage; **+1.3 MB** for the whole corpus |
| Determinism, offline | **1.000** (5/5 runs) | answer + verifications byte-identical; timings excluded, see §8.2 |
| Abstention rate, 3 unanswerable questions | **0.000** | see §8.3 — this is the bad number |
| Fabrications on abstention | **0** | invariant held |
| False-abstention rate | 0.000 (9 answerable) | |
| Inter-annotator agreement | **0.958** (23/24) | hand-labelled set |

**Verification still discriminates.** Eight claims against one retrieved passage:

| Claim | Label | Support | Reason |
|---|---|---|---|
| verbatim copy | Verified | 1.000 | `supported` |
| near paraphrase | Verified | 0.632 | `supported` |
| correct words, wrong page | Unsupported | 0.000 | `page_mismatch` |
| negation flipped | Needs Review | 0.000 | `contradiction_detected` |
| wrong year | Unsupported | 0.000 | `numeric_mismatch` |
| unrelated topic | Unsupported | 0.000 | `no_support` |
| fabricated `[S7, p.1]` | Unsupported | 0.000 | `unresolvable_reference` |
| partially wrong | Needs Review | 0.000 | `contradiction_detected` |

### 8.2 Determinism needed its method corrected to be honest

The first version compared the full serialised response and reported **0.2**. The only fields that
differed were the five `QueryMetrics` wall-clock timings, which are different every time they are
taken — comparing them measures the clock, not the system.

The claim actually worth making is narrower, and is now what the test asserts: the question, answer,
claims, retrievals, verifications, summary and warnings are **byte-identical across five runs**. Both
figures are recorded so the change of method is visible rather than buried.

### 8.3 The abstention result is bad, and is reported as bad

**The offline profile does not know when it does not know.** Asked about mercury's boiling point, the
2019 Cricket World Cup, and photosynthesis — none of them anywhere in the report — it answered all
three, quoting the least-irrelevant sentence it could find, at mean support **0.59** across 9 claims.

This is not a defect in the abstention *path*, which is implemented and tested: an empty index
produces a correct abstained response. It is a limitation of the extractive generator's trigger, which
asks "is any sentence relevant enough?" and never asks "do these passages answer the question?".
TF-IDF cosine between unrelated English sentences is near zero but not exactly zero, so something
always clears the bar.

The consequence is worse than a high false-abstention rate would be: the failure mode is a confident
answer with genuine citations drawn from irrelevant passages — the *appearance* of an informed
system. Recorded as **R-24**. Threshold calibration does not fix it; it needs a relevance floor on the
retrieved set, which was not attempted.

### 8.4 Explicitly not measured

| Metric | Why |
|---|---|
| Model load time | No weights on this machine, so no model is ever loaded. Any figure would be invented. |
| Semantic-profile latency and Recall@k | MiniLM weights absent. The offline-vs-semantic ablation the report would like is unavailable. |
| FLAN-T5 marker coverage | The abstractive generator never ran. |
| Semantic determinism | Requires MiniLM. |

These are the measurements the offline guarantee makes impossible. Saying so is the honest result,
and each is a sentence the report must not fill with an estimate.

### 8.5 Earlier figures, kept for the record

| Item | Value | Method | Date |
|---|---|---|---|
| Stage 1 report | 11 pages, 22,315 bytes of text | `pdfplumber` page-by-page | 2026-10-08 |
| Stage 2 report | 15 pages, 32,911 bytes of text | `pdfplumber` page-by-page | 2026-10-08 |
| Pinned Python | **3.14.6** | `.venv\Scripts\python.exe --version` | 2026-10-08 |
| Clean-venv install | 110 packages from `requirements.txt`, exit 0 | `pip install -r requirements.txt` | 2026-10-08 |
| `chromadb` | **1.5.9, working** | import + `add` + `query` + reopen-and-count | 2026-10-08 |
| Phase 2 synthetic fixture | 5 pages → 5 chunks, 48 words | `chunk_pages` at 180/30 | 2026-10-08 |
| Phase 3 smoke-test indexing | 0.258 s per 100 pages | 5 docs / 25 pages, **synthetic one-line pages** | 2026-10-08 |
| Phase 3 smoke-test query | p50 0.8 ms, p95 2.1 ms | 25-chunk synthetic corpus | 2026-10-08 |
| Chroma restart without re-reading | store count 5, `restored_chunks` 5, top hit page 4 | fresh pipeline, `load_document` monkeypatched to raise | 2026-10-08 |
| Open-source candidates | 18 | Phase 0 research | 2026-10-08 |
| Strategy B score | 9.00 / 10 | weighted scoring | 2026-10-08 |
| MiniLM `max_seq_length` | 256 | Hugging Face API | 2026-10-08 |
| Git | 2.55.0.windows.3, **no repository here** | `git --version`, `git status` | 2026-10-08 |

The two Phase 3 latency rows are superseded by §8.1 and are kept only so the progression is visible.
The synthetic one-line-page corpus gave roughly 6× faster figures than the real report; quoting them
beside the real ones would flatter the system.

---

## 9. Next action

> **Phase 7 is under way.** Items 7.1, 7.3, 7.5, 7.7 and 7.8 are done. The rest need a human.

### Done in Phase 7 so far

| Item | Result |
|---|---|
| 7.1 Evidence tracker complete | **done.** Every row carries a real artifact or an explicit "not measured". Remaining gaps are screenshots and CI, both recorded as gaps |
| 7.3 Reproducible logs | **done.** 9 captured outputs in [logs/](../logs/README.md), each with the command that regenerates it |
| 7.5 Report drafted from the tracker | **done, as a draft.** [16_STAGE_3_REPORT_DRAFT.md](16_STAGE_3_REPORT_DRAFT.md), 15 sections, no number that lacks a log |
| 7.6 Viva script rehearsed | **done, on paper.** Beat 4 rewritten after R-24 was measured ? it promised an abstention that does not happen. New ?4.5 with the three questions Phase 6 made newly answerable |
| 7.7 I-01 citation numbering | **closed by measurement.** The Stage 0 suspicion did not reproduce: `Magesh`, `legal research`, `hallucination-free` occur 0 times in the Stage 2 text, and a citation audit found 0 dangling and 0 orphaned references. R-04 closed |
| 7.8 Deviations log | **done.** D-11 ? D-19 in [01 ?3.1](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log) |

### Still open, and what each needs

| # | Item | Needs | Who |
|---|---|---|---|
| 7.2 | **Screenshots S1?S9** | someone at a screen running `streamlit run app.py`. Nine captures, each labelled *captured* with a timestamp. None will be fabricated, so the report currently has no screenshots and says so | Human |
| 7.4 | **Contribution table** | **B-05**: `git init`, a remote, and a decision on authorship. `git log --author=` currently has no output, so ?13 of the report is empty | Human |
| 7.6b | R-23 manual UI checks | greyscale, keyboard-only, 1280/768 px. Three pairs of eyes | Human |
| ? | CI run | follows from B-05 (B-08) | Human |
| ? | Semantic-profile figures | MiniLM + FLAN-T5 weights, and a decision about whether to download them at this stage | Human |

### Carry these forward, because they are what the report must not hide

- **R-24 — MITIGATED, not closed.** Was 0.000; now **0.750** correct abstention with **0.000** false, after a
  gate that refuses *before* generation (§7.5). The **6 adversarial cases still get confident answers** and
  stay in the labelled set so the headline number cannot be improved by deleting them. Closing that needs
  entailment, not a better threshold.
- **B-05 — partially resolved.** A repository exists and CI is green; `9772226` still carries the placeholder
  author, so §13 of the report stays a disclosure rather than a per-member split.
- **B-08 — closed.** CI green, run 37880879892 on `66075b`, all three jobs success.
- **R-23 ? the UI has not been seen.** 98 automated tests prove the render path executes. That is not the same as a readable layout.
- **The calibration rests on 24 self-authored, self-labelled cases.** It justifies 0.63; it does not prove it. The recorded 0.958 "agreement" is a self-reconciliation, not independent labellers, and is described that way everywhere it appears.
- **The 6 `semantic` tests have never run.** If the team can reach Hugging Face, run them once and record the result ? pass or fail.
- **B-07 ? the fixture PDF is outside the repository.** `tools/evaluate.py` and `tools/measure.py` skip without it, so the calibration is not reproducible on a fresh clone until someone decides whether the report may be committed.
- **B-05 ? still no git repository.** Nothing is committed, so nothing in this report can cite a commit hash, and ?13 stays empty.

## 10. Session handoff notes

For the next agent session, in order:

1. Read [AGENTS.md](../AGENTS.md) in full.
2. Read §1 and §9 of this file.
3. Confirm `APPROVE PHASE 7` is in the conversation. If not, stop and ask.
4. Read [06 §8](06_IMPLEMENTATION_ROADMAP.md#8-phase-7--stage-3-readiness) for scope and
   [12_STAGE_3_EVIDENCE_TRACKER.md](12_STAGE_3_EVIDENCE_TRACKER.md) — the report is drafted *from*
   that document, never from memory.
5. Run tests with `.venv\Scripts\pytest.exe -q`. The pinned environment is where the 429 passing
   tests were observed.
6. `tools/evaluate.py` and `tools/measure.py` need the Stage 2 report at
   `~/Downloads/.pdf/FAI_PE_Microproject_Stage_2_Report_Revised.pdf`. Without it they skip, and
   B-07 must be resolved before a fresh clone can reproduce the calibration.
7. Do **not** commit, push, or create a remote without explicit approval. B-05 blocks both the
   contribution table and CI.

### Reusable temporary artifacts

Phase 0 used a throwaway PDF text extractor at `%LOCALAPPDATA%\Temp\opencode\extract_pdf_text.py`
and Phase 2 added `chroma_smoke.py` there. Both are throwaway and neither is project code.

The equivalents that matter now live in the project:

| Purpose | Where it lives now |
|---|---|
| Build a PDF without a blob in git | `tests/conftest.py::build_pdf` |
| Index, ask, verify from a shell | `run_demo.py` |
| Score the labelled set, sweep the threshold | `tools/evaluate.py` |
| Rebuild the labelled set from the fixture | `tools/build_cases.py` |
| Measure latency, RSS, Recall@k, determinism | `tools/measure.py` |
| Start the app headless | `streamlit run app.py --server.headless true` |

## 11. Change log
| 2026-10-09 | 7 | **R-24 closed: evidence-based abstention.** Audit first, code second. Rejected a floor on `relevance_score` after measuring that answerable and unanswerable cosine ranges overlap (any floor catching most unanswerable questions killed ≥5 of 8 answerable). Shipped `query_coverage` instead — fraction of the question's content words present in the retrieved passages — gated in `ask()` **before generation**, floor `0.50` in `AbstentionConfig`, swept 0.00→1.00 on a new 48-case labelled set (24 answerable naming their page, 24 unanswerable incl. **6 adversarial**). Measured: correct abstention **0.000 → 0.750**, false abstention **0.000**, false-`Verified` on the original 10 questions **15 → 0**, claims emitted on them **50 → 0**, answerable claims **unchanged**. Also: `GeneratedAnswer.notes` silently accepted a bare `str` (UI rendered single letters) — now coerced. **429 passed, 6 deselected.** ADR-0014 added; 14 docs updated; 24 tests added, none weakened |

| Date | Phase | Change |
|---|---|---|
| 2026-10-08 | 0 | Workspace + environment audit; reference PDFs located and extracted; 18 candidates evaluated with live API evidence; strategy B selected |
| 2026-10-08 | 1 | Full documentation knowledge base created (18 files + `docs/reference/`) |
| 2026-10-08 | 2 | ADR-0001 accepted (Python 3.14.6); `.venv` + pinned `requirements.txt`; `chromadb` verified; `src/models.py`, `src/pdf_ingestion.py`, `src/chunking.py` written; `tests/test_core.py` with 56 tests, all passing; gate G2 passed |
| 2026-10-08 | 3 | `src/embeddings.py`, `src/vector_store.py`, `src/pipeline.py` written; `RetrievalResult`/`IndexStats`/`PipelineConfig` added to `src/models.py`; fixtures extracted to `tests/conftest.py`; `tests/test_retrieval.py` added (80 tests); `pytest.ini` registers the `semantic` marker; **144 passed, 4 deselected**; gate G3 passed |
| 2026-10-08 | 5 | `app.py` written - three surfaces, all activity states, namespaced CSS design system; `reconfigure()` and `last_report` added to the pipeline; `tests/test_ui.py` (98 tests) + `tests/app_under_test.py` shim; **325 passed, 6 deselected**; gate G5 passed with 3 manual items pending; 13 contrast ratios measured |
| 2026-10-08 | 6 | `run_demo.py` (FR-48/49); `tools/build_cases.py` + `tools/evaluate.py` -> **24-case hand-labelled set**, every passage verbatim-checked; `tools/measure.py` -> 13 metrics on the real 15-page report; `tests/test_hardening.py` (46 tests); `.github/workflows/tests.yml`; **405 passed, 6 deselected**; gate G6 passed except CI (B-05). `verified_threshold` 0.62 -> **0.63**; false-`Verified` 0.125 -> **0.000**. Two verifier defects found by the evaluation and fixed |
| 2026-10-08 | 6 | Documentation reconciliation after the gate: repaired duplicated/misnumbered headings in this file, filled the Phase 4-6 evidence rows in 01/12/13, measured results into 10 ?11 and 12 ?9, retired R-01/R-11/R-15, added **R-24** (abstention 0.000) and A-06/A-07, corrected `labeller_a`/`labeller_b` to be described as a self-reconciliation rather than independent annotators, and fixed 2 broken cross-links. No product code changed; suite re-run green at 371 passed |
| 2026-10-08 | 7 | `logs/` created with 9 captured command outputs + README; **[16_STAGE_3_REPORT_DRAFT.md](16_STAGE_3_REPORT_DRAFT.md) drafted from the tracker**; [01 ?3.1](01_REQUIREMENTS.md#31-stage-3-versus-stage-2-deviations-log) D-11->D-19; **I-01 checked and did not reproduce** - R-04 closed; viva beat 4 rewritten after R-24; tracker ?9 rewritten for Phase 7. Gate G7 **not passed**: 7.2 screenshots and 7.4 contributions need a human |
| 2026-10-08 | 7 | **Three live verifier defects found and fixed** (antonym branch searched `claim & chunk`, which by construction excludes the token an antonym contradiction turns on; the negation guard read a stopword-filtered set in which `not` can never appear; the antonym list paired inflections individually so cross-forms never met). Inflections now grouped by concept with seven named oppositions, and the check declines when the passage uses the claim's own direction. Accuracy unchanged at 0.667, threshold unchanged at 0.63, so no re-calibration was needed and none is claimed. 31 direct tests; **405 passed, 6 deselected**. **R-25 stays open**: the antonym branch is correct code and unit-tested, but no labelled case exercises it |
