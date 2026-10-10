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
| **G7 blocked on** | **B-05** (placeholder author ⇒ no per-member contribution table), **B-07 residual**, the 6 adversarial abstention misses, and the 4 manual UI states (greyscale, keyboard-only, 1280 px, degraded). Screenshots S1–S5 are **captured** |
| **Tests written** | **512** across `test_core.py` (64), `test_retrieval.py` (87), `test_verification.py` (136), `test_ui.py` (98), `test_hardening.py` (64), `test_generalisation.py` (63) |
| **Commits made** | **2** — `fd2be70` (Phase 7, attributed) and `9772226` (Phases 0–6, **placeholder author**, B-05) |
| **CI** | **GREEN.** Run [37880879892](https://github.com/Purv-Jain/Aries/actions/runs/37880879892) on `66075b`: `offline (ubuntu-latest)`, `offline (windows-latest)`, `security-sweep` all **success**. B-08 closed |
| **Model weights downloaded** | **2** — `all-MiniLM-L6-v2` (91.6 MB) and `flan-t5-small` (311.1 MB), fetched 2026-10-10 via `HF_HUB_DISABLE_XET=1` |
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
| 6 | Testing + hardening | **DONE** | Bhavya | G6 **passed**, CI green | `pytest -q` → 512 passed (492 + 20 skips without the calibration report); see §7 |
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
| ~~**B-07**~~ | **PARTIALLY CLOSED.** The Stage 2 report is deliberately **not** committed — it is the team's submission and names PRNs, and the repo is public. Its sha256 is recorded so numbers are checkable. A **synthetic 9-PDF fixture corpus (35 KB) is committed** and 63 generality tests now run on a fresh clone. The 34-case calibration still needs the real report: 492 passed + 20 skipped without it | §7.8 | **Residual open** — closing the calibration half needs a human decision on publishing the report |
| ~~B-08~~ | ~~`ubuntu-latest` CI job fails~~ | Gate G6 item | **RESOLVED AND VERIFIED 2026-10-09.** Cause: `PROJECT_ROOT / r"tests\data\eval_cases.jsonl"` resolves to a *single filename* on POSIX, where a backslash is a legal filename character. The nine `TestEvaluationSetIntegrity` tests called `_load_cases()` with no skip guard, so they raised `FileNotFoundError` instead of skipping — which is why the job failed rather than silently under-reporting. Fixed in PR #1 and in `66075b` (the identical literal in `tools/build_cases.py`). **Verified green**: run [37880879892](https://github.com/Purv-Jain/Aries/actions/runs/37880879892) on `66075b`, all three jobs `success`. `TestPathsAreCrossPlatform` fails on any reintroduction | — |

**B-05 is partly resolved** — the repository exists and Phase 7 is correctly attributed; the
Phase 0–6 commit keeps its placeholder author by deliberate decision. **B-08 is resolved and verified green** — the ubuntu failure was a Windows path literal that made the
evaluation tests raise `FileNotFoundError`, found and fixed via PR #1. Run 37880879892 is green on all three jobs.

Remaining blockers and what each needs:

| # | Needs |
|---|---|
| **B-05** | Post-submission history rewrite, or leave it — disclosure is already in report §13 |
| **B-07** | ~~A decision on whether the fixture PDF may be committed~~ — **decided: it may not be** (public repo, PRNs). A synthetic corpus is committed instead; the residual needs a human to publish the report privately or accept the 20 skips | §7.8 |
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
| — | all | `pytest -q -m semantic` | Semantic | **6 passed**, 38.4 s, 2026-10-10. Two live defects found and fixed on the first run — see §7.7 |

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
| FR-17 MiniLM 384-dim | `TestSemanticProfile` | **4 passed** — after fixing the 1-D query defect that broke every semantic query |
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
| 0.30 | 0.600 | 0.923 | 0.727 | **0.400** | 0.676 |
| 0.45 | 0.750 | 0.923 | 0.828 | 0.250 | 0.706 |
| 0.57 | 0.846 | 0.846 | 0.846 | 0.154 | 0.676 |
| 0.59 | 0.917 | 0.846 | 0.880 | 0.083 | 0.706 |
| **0.63** | **1.000** | **0.846** | **0.917** | **0.000** | 0.706 |
| 0.70 | 1.000 | 0.769 | 0.870 | 0.000 | 0.676 |
| 0.80 | 1.000 | 0.462 | 0.632 | 0.000 | 0.588 |
| 0.85 | 1.000 | 0.077 | 0.143 | 0.000 | 0.441 |
| 0.87 | 0.000 | 0.000 | 0.000 | 0.000 | 0.412 |

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

## 7.6 The antonym branch — R-25 closed

**Phase 7, 2026-10-09.** R-25 was right that the 24-case set contained no antonym pair. Ten cases
were added from real report passages, and the branch was measured for the first time.

### What the cases found that 31 unit tests could not

`ant_08` and `ant_09` were reported `contradiction_detected` against passages that never mentioned
the claim's subject. `ant_09` told the user the source contradicted a claim about paid API
expenditure, when the source was a table row about reducing blind trust that happened to contain the
word "reduces". A confident, wrong explanation is worse than a missed contradiction, so a subject
gate was added: an antonym counts only if the claim is about the **sentence carrying it**, with a
single-sentence exemption so minimal pairs like "It was profitable." / "It was expensive." keep
firing. [ADR-0015](05_TECH_STACK_AND_ADRS.md#adr-0015--an-antonym-is-only-a-contradiction-if-it-is-about-the-same-thing).

### Measured

| | Before | After |
|---|---|---|
| Labelled contradictions detected | 0 of 0 (no cases existed) | **4 of 4** |
| Non-firings correctly silent | 0 of 0 | **6 of 6** |
| `ant_08` / `ant_09` reason code | `contradiction_detected` (wrong) | `weak_support` / `no_support` (right) |
| Accuracy over the labelled set | 0.667 (24 cases) | **0.735** (34 cases) |
| `Verified` recall | 0.800 | **0.846** |
| `Verified` F1 | 0.889 | **0.917** |
| `Verified` precision | 1.000 | 1.000 |
| False-`Verified` | 0.000 | **0.000** |
| Chosen threshold | 0.63 | **0.63** |

The threshold did not move. That is a good sign for the calibration and not proof that 0.63 is
right. All 24 pre-existing cases produce byte-identical results before and after — verified by
diffing `eval_results.json` against `HEAD`.

### What the gate cannot do

It is a lexical proxy for "about the same thing". A claim and a passage about the same subject in
entirely different vocabulary are still missed. And it is a decline rule, so it can only remove
detections — asserted by a test that sweeps 100+ word pairs and checks the guarded result set is a
subset of the unguarded one.

**Tests added: 12** — 6 on the subject gate in `test_verification.py` (including the subset
property and the minimal-pair exemption) and 6 in `test_hardening.py` (the labelled set really
contains antonym pairs, exactly the four fire, all six non-firings decline for a named reason, and
the two end-to-end label assertions). No existing test weakened; the 6 call sites that used the old
three-argument `_antonym_conflict` signature were updated to pass passage text.

## 7.7 Semantic validation — the six tests ran, and found two live defects

**Phase 8, 2026-10-10.** `pytest -q -m semantic` had never been executed. It now has been, and the
result is not the reassuring one the plan assumed.

### Getting the weights down

`huggingface.co` was reachable, and `torch 2.13.0+cpu`, `transformers`, `sentence-transformers` and
`onnxruntime` were all installed. The download nevertheless appeared to hang: two attempts ran for
15 and then 40 minutes and left a 63.88 MB `.incomplete` file whose timestamp never moved.

**The cause was not bandwidth.** A ranged HTTP request for the same file returned 4.19 MB in 3.2 s
(**1.29 MB/s**) from `us.aws.cdn.hf.co`. The stall was in the **Xet transport** that
`huggingface_hub` prefers by default. Setting `HF_HUB_DISABLE_XET=1` forced the classic HTTP path
and both models downloaded in under a minute.

That is worth recording as a portability finding: on this machine, on this network, the default
Hugging Face download path does not work and one environment variable fixes it.

### First run: 2 passed, 4 failed

| | Result |
|---|---|
| `test_minilm_produces_384_dimensional_unit_vectors` | **passed** |
| `test_cosine_rescaling_is_off_for_tfidf_and_on_for_minilm` | **passed** |
| `test_semantic_similarity_is_rescaled_to_zero_one` | **FAILED** `ValueError: Expected 2D array, got 1D array instead` |
| `test_unrelated_text_scores_lower_than_related_text` | **FAILED** — same |
| `test_minilm_end_to_end_retrieval_finds_the_right_page` | **FAILED** — same |
| `test_minilm_similarity_feeds_the_support_score` | **FAILED** — same |

### The defect

`MiniLMEmbeddingBackend.embed_query` returns `embed_documents([text])[0]`, which is a **1-D** `(384,)`
array. `embed_documents` returns a **2-D** `(n, 384)` matrix. `similarity()` passed the 1-D query
straight to `sklearn.metrics.pairwise.cosine_similarity`, which rejects it.

**Every semantic query raised.** `PipelineConfig(embedding_backend="minilm")` could not answer a
single question.

Six phases of green tests did not catch it, and the reason is the point:

* the six tests that would have caught it are deselected whenever the weights are absent — which is
  every run, including every CI run;
* the TF-IDF backend returns a sparse `(1, n)` matrix from `embed_query`, so it never trips the bug;
* all 441 offline tests passed throughout.

A defect can be invisible for exactly as long as nobody runs the path that contains it.

Fixed by reshaping a 1-D query to one row, with **7 weights-free regression tests** added
(`TestMiniLmSimilarityShapes`). They build plain arrays and stub `_load`, so they run in CI where
no model exists — a guard that needed the weights it guards would have been no guard at all. The
guard also asserts its result set is identical for 1-D and 2-D queries, and pins the 1-D/2-D
asymmetry itself so a future "tidying" of `embed_query` fails deliberately rather than silently.

**After the fix: 6 passed.** `449 passed, 6 deselected` offline, unchanged.

### M8 is now a measurement, not a prediction

| Figure | Measured |
|---|---|
| MiniLM load (warm cache) | **5.48 s** |
| MiniLM, one sentence | **68.2 ms** |
| MiniLM encoding, 46 chunks | **2.791 s** (60.7 ms/chunk) |
| MiniLM query encode | **29.5 ms** |
| FLAN-T5 tokenizer load | **1.85 s** |
| FLAN-T5 model load | **0.93 s** |
| FLAN-T5 greedy generation | **0.683 s** |
| Weights on disk | MiniLM **91.6 MB**, FLAN-T5 **311.1 MB** |
| Resident memory | 330.5 MB baseline → 480.6 after MiniLM → 589.3 after FLAN-T5 |
| Device | CPU only, `torch.cuda.is_available() == False`, 6 threads |

Single run, CPU, no GPU. Each figure is one measurement, not an average.

### The finding that matters: MiniLM did not beat TF-IDF

Same 9 hand-authored questions, same 15-page report, same store.

| | TF-IDF | MiniLM | MiniLM better? |
|---|---|---|---|
| Recall@1 | 0.667 | 0.667 | **no** |
| Recall@3 | **1.000** | 0.889 | **no** |
| Recall@5 | 1.000 | 1.000 | no |
| Recall@10 | 1.000 | 1.000 | no |
| MRR | 0.778 | **0.806** | yes |
| Retrieval p50 | **~2 ms** | ~31 ms | — |
| Full `ask()` p50 | ~12–37 ms | ~494 ms | — |
| Peak RSS | **192.6 MB** | 589.3 MB | — |

Identical at Recall@1, worse at Recall@3, marginally better at MRR, for roughly **15x** the retrieval
latency and **3x** the memory. The question it lost is instructive: *"How large is the FLAN-T5-small
weight file?"* — TF-IDF puts page 9 first on the lexical anchor, MiniLM ranks it fourth, because the
size is stated in a table and there is no semantic relationship between "large" and "308 MB".

**This is the measured justification for the project's central design decision**, which until now was
an argument rather than a result: the semantic profile is an option, and on this evidence the offline
profile should be the default. Nine questions against one document cannot settle MiniLM versus
TF-IDF in general, and nothing here claims they do.

### What is still not measured

The semantic profile's *verification* quality end to end, and FLAN-T5's effect on citation markers
through the pipeline. Both need a semantic-profile run of the labelled set, which is a larger job
than Phase 8 and is not claimed here.

## 7.8 B-07 — fixtures in the repository, and a generality question worth asking

**Phase 8, 2026-10-10.** B-07 was filed as "the calibration PDF lives outside the project". Fixing it
surfaced a larger question: *is the system calibrated against one document, or does it work on
reports nobody here has read?* A fixture that reproduces our own numbers proves the first and says
nothing about the second.

### What was committed, and what deliberately was not

**Not committed: the Stage 2 report.** It is the team's own academic submission; it names its
authors, their PRNs and their project guide; and this repository is public. Publishing it is not a
decision an agent should make. Its identity is recorded instead, so any number in the report can be
checked rather than taken on trust:

```
sha256  307ed3242ff3d1f7321800c7d86c3eb21575b36032490b0d3de23368e985d687
bytes   764646
pages   15  →  46 chunks
```

**Committed: a synthetic fixture corpus**, [tools/build_fixtures.py](../tools/build_fixtures.py) →
`tests/data/fixtures/`. Nine PDFs, **35 KB in total**, every byte synthesised from literal strings in
that script — no third party's document, no team names, no PRNs. All nine are committed rather than
generated on demand, because a test that needs a build step before it can pass is a test a fresh
clone never ran.

| fixture | hazard it exists for | extraction |
|---|---|---|
| `single_column` | the control | 4 pages, 1,364 chars |
| `two_column` | naive extraction interleaves columns mid-sentence | 4 pages, 1,364 chars |
| `wide_table` | space-padded rows match the wrong quantity | 4 pages |
| `long_page` | a page far longer than normal, chunk boundaries | 4 pages, 11,923 chars |
| `hyphenated` | words broken across a line break | 4 pages |
| `unicode` | em dash, curly quotes, accented Latin-1 | 4 pages |
| `headers_footers` | a running head on every page | 4 pages |
| `scanned` | no text layer | **refused** — `scanned_pdf` |
| `encrypted` | password protected | **refused** — `encrypted_pdf` |

### A defect this found, in the test harness rather than the product

The first `unicode` fixture came back with the em dash and both curly quotes **lost** — while the
surrounding English read perfectly, so a word-level assertion would have passed.

Checking the **raw content-stream bytes** rather than trusting the extracted text located it: the
stream contained literal `?` (0x3F) where the characters should have been. The cause was in
`tests/conftest.py`, which encoded the content stream as **ISO-8859-1 against a font declaring
`/WinAnsiEncoding`**. Those two are not the same codec: U+2014, U+201C and U+201D are absent from
ISO-8859-1 entirely and were replaced at *write* time. Accented characters survived precisely because
they *are* in ISO-8859-1 — which is why the defect looked like an extractor bug and was not one.

Fixed by encoding as `cp1252`, the correct pairing. All six characters now survive extraction, and
all 512 offline tests still pass, so the change is a strict improvement rather than a swap.

**A system can be innocent and still be wrong, and the way to tell is to look at the bytes.**

### What the generality suite actually asserts

[tests/test_generalisation.py](../tests/test_generalisation.py), **63 tests**, for each extractable
fixture: pages come out, page numbers are contiguous and one-based, every citation resolves, no
claim is `Verified` without one, retrieval finds the page the answer is on, output is byte-identical
across three runs, and — the one that matters most — **abstention still fires** on a topic absent
from that document.

That last one is a generalisation test rather than a smoke test. The `min_query_coverage` floor was
calibrated on the Stage 2 report; if it only worked there, it would be a property of that document
instead of of the system. It does not: all three out-of-corpus questions abstain on all seven
extractable fixtures.

### The boundary, asserted so it cannot drift

`TestWhatThisSuiteDoesNotClaim` names six things this does **not** cover — OCR'd scans, right-to-left
and CJK scripts, rotated pages, tracked-change layers, multi-document cross-citation, and anything
needing a layout model — and asserts each appears in the module docstring, so the coverage claim and
the code cannot disagree.

Nine synthetic fixtures are not nine real papers. The honest summary is *"no error on the hazards
listed above"*, not *"works on every research report"*.

### Fresh-clone reality, measured both ways

| | with the Stage 2 report | without it |
|---|---|---|
| offline suite | **512 passed**, 0 skipped | **492 passed, 20 skipped** |
| 6 `semantic` | pass | pass (weights on disk) |
| generality | 63 pass | 63 pass |

The 20 skips are exactly the `@needs_fixture` calibration tests, each printing its reason. They skip;
they are never counted as passes. Reporting "0 skipped" without that condition would have been
precisely the kind of claim this project exists not to make — it is true only on a machine that
happens to hold the file.

### Also fixed

`README.md` documented `python tools/evaluate.py` as sweeping the threshold. It does not — that needs
`--sweep` — and running it with `--json tests/data/eval_results.json` **silently deleted the 1,925-line
sweep block** from the committed calibration record. Found in Phase A, reproduced and confirmed here.
The documented command now carries `--sweep`, and `tools/evaluate.py` explains the consequence.

## 7.9 UI evidence — five real screenshots

**Phase 8, 2026-10-10.** S1–S5 were captured by launching the actual application and driving it, not
by describing it.

| # | File | State | Bytes |
|---|---|---|---|
| S1 | `docs/screenshots/S1_dashboard_empty.png` | Dashboard before any upload — the real empty state | 244,633 |
| S2 | `docs/screenshots/S2_library_indexed.png` | Indexed document library, after a real upload | 234,418 |
| S3 | `docs/screenshots/S3_answer_with_citations.png` | Grounded answer with `[Sx, p.y]` markers | 323,529 |
| S4 | `docs/screenshots/S4_verification_evidence.png` | Per-claim verification, cited passage open | 335,149 |
| S5 | `docs/screenshots/S5_abstention.png` | Out-of-corpus question refused | 304,587 |

1440x900 viewport, 2x device scale, captured by
[`tools/capture_screenshots.py`](../tools/capture_screenshots.py). Regenerating is one command and
nothing was hand-edited afterwards.

**Which document, and why it matters.** The captures use the committed synthetic fixture, **not** the
team's Stage 2 report. Screenshots of that report committed to a public repository would publish it
— its authors, their PRNs, their guide — and would undo the decision §7.8 declined to make. A test now
asserts the capture script never reads it, so this cannot be undone quietly later.

**S5 is the Phase B gate, on screen.** It shows *"No answer was produced"*, the coverage figure against
the 0.50 floor, the specific query terms that did not match (`boiling`, `level`, `mercury`, `point`,
`sea`), and a verification panel reading 0/0/0 with *"Nothing to verify — the answer was abstained
on."* R-24 was closed by a number; this is the same behaviour as a user meets it.

### Three harness defects found on the way, all of which pointed at the app

1. **Waiting for the status widget to disappear.** On first load the widget does not exist yet, so
   `count() == 0` means *has not started*, not *has finished*. The first failure read "the Dashboard
   is missing", which sends you looking at `app.py`.
2. **A fixed poll interval.** It gave up at 16 s; a cold Streamlit render on this machine takes
   about 18 s. Same misleading error.
3. **`page.content()` versus `inner_text`.** They do not agree on this build: `content()` reported
   the library filename but not the workspace's empty-state note; `inner_text` the reverse. Using
   only one produced a false "the panel never rendered", **twice, in opposite directions**.

The fix is to wait for the content that must be there and match it against **either** measure. Each
failure named the harness rather than the application, which is the whole difficulty: a screenshot
harness that misreports its own timing produces fabricated-looking evidence of a broken app.

### Keeping them honest

`TestScreenshotsAreEvidence` (12 tests) asserts each file exists, is a complete PNG ending in `IEND`,
is not a blank rectangle (a failed render produces a valid, tiny, uniform PNG), and that the set
matches what the report cites. It **cannot** tell whether a picture is honest — only a person can — and
it is described that way rather than oversold.

### Also fixed

The SEC-04 sweep failed on the new capture script, correctly: it shells out to start Streamlit. The
sweep already carried a named allowlist designed for exactly this (*"the single exception ... named
here so that adding a second one would be visible"*). Rather than narrow the sweep, the allowlist
became a `path -> reason` map, each entry now states **why** it is exempt, the `shell=True` ban was
extended to every exempt file, and a reverse check fails if an exempt file stops shelling out so the
list cannot drift. The same enforcement, with less room to abuse.

### Still manual

S6–S9 — greyscale legibility, keyboard-only traversal, a 1280x768 viewport, and the degraded-mode
banner — are the four states a machine cannot honestly certify. 98 UI tests prove the render path
executes; they cannot see a layout. Those remain open, and are listed as open.

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
| 7.2 | ~~**Screenshots S1–S9**~~ | **S1–S5 captured 2026-10-10**, real, by `tools/capture_screenshots.py` driving a real Streamlit process; a test fails if any goes missing, truncates or blanks out. S6–S9 (greyscale, keyboard-only, 1280 px, degraded) still need a person | §7.9 |
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
- ~~The 6 `semantic` tests have never run.~~ **Done 2026-10-10** — 6 passed. But MiniLM measured **no better than TF-IDF** on this fixture (§7.7), which is the finding that matters.r fail.
- **B-07 — partially closed.** A synthetic 9-PDF fixture corpus is committed and 63 generality tests run on a fresh clone, but the 34-case calibration still needs the team's own report, which is deliberately not published. Without it: 492 passed, 20 skipped, each skip printing its reason
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
| 2026-10-10 | 8 | **UI evidence captured.** `tools/capture_screenshots.py` starts a real Streamlit process, uploads the committed synthetic fixture and photographs five real states — empty dashboard, indexed library, grounded answer with citations, per-claim verification with the cited passage, and an out-of-corpus refusal that names the query terms which did not match. Captured on the **synthetic fixture, not the Stage 2 report**, because screenshots of that report in a public repository would publish it. Three harness defects found and fixed, each of which had produced a misleading "the panel never rendered" failure: waiting on a status widget that does not exist yet on first load, a fixed 16 s poll against an 18 s cold render, and `page.content()` disagreeing with `inner_text` in both directions. 12 new tests keep the set honest (complete PNG, not a blank rectangle, set matches the report). SEC-04's allowlist became a path-to-reason map with a reverse check. **524 passed** |
| 2026-10-10 | 8 | **B-07 partly closed; generality is now a measurement.** Nine synthetic PDFs (35 KB, all committed) covering two-column pages, space-padded tables, a very long page, hyphenation, non-ASCII, running headers, a scanned page and an encrypted file; **63 tests** assert the whole path on each — extraction, page numbering, citation resolution, retrieval of the answering page, determinism, and that **abstention still fires** on topics absent from each document, which is what proves the coverage floor is not a property of the Stage 2 report. The Stage 2 report itself is **deliberately not committed** (public repo, PRNs); its sha256 is recorded. Found and fixed a **harness** defect: `tests/conftest.py` encoded PDF content streams as ISO-8859-1 against a font declaring `/WinAnsiEncoding`, silently replacing em dashes and curly quotes with `?` at write time — accented letters survived, so it looked like an extractor bug and was not. Now cp1252. Also fixed the Phase A finding that `tools/evaluate.py` does not sweep without `--sweep` and silently deletes the committed sweep block. **512 passed** with the report, **492 + 20 skips** without. 63 added, none weakened |
| 2026-10-09 | 7 | **R-25 closed: the antonym branch is measured, and a fourth defect falls out.** Ten labelled antonym cases (`ant_01`-`ant_10`) authored from real report passages; four must fire the contradiction check and six must not, each for a different named reason. Measured: **4/4 contradictions detected, 6/6 non-firings silent**. Adding them exposed a defect the 31 unit tests could not see — a claim about *any* subject was reported contradicted if the passage contained an opposite direction word anywhere, so `ant_09` (“The paid API expenditure increased after Stage 2”) was labelled `contradiction_detected` by a table row about blind trust. A false contradiction is worse than a missed one, so a subject gate now requires the claim to be about the sentence holding the antonym, exempting single-sentence passages so minimal pairs still fire; a test asserts the gated result set is a *subset* of the ungarded one over 100+ word pairs. Accuracy **0.667 → 0.735**, `Verified` recall 0.800 → 0.846, F1 0.889 → 0.917, precision 1.000, false-`Verified` 0.000, **threshold still 0.63**. Also documented a reporting trap: the sweep holds `review_threshold` at verified/2, so its accuracy column reads 0.706 against the shipped configuration's 0.735. ADR-0015 added. **441 passed, 6 deselected.** 12 tests added, none weakened |
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
