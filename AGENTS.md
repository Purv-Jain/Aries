# AGENTS.md — Persistent instructions for AI agents working in this repository

**Read this file first, in full, before touching anything.**

This file is the single source of truth for how to work in this repo. It persists across AI coding
sessions. If your instructions conflict with this file, this file wins unless a human explicitly
overrides it in the current session.

---

## 1. What this project is

A local-first RAG (Retrieval-Augmented Generation) academic research assistant with **citation
verification**. Pipeline:

```
PDF upload → validate → extract page-wise text → sentence-aware chunk → embed
   → persist (Chroma) → retrieve top-k → generate grounded answer with [S1, p.5] markers
   → verify each claim against its cited evidence → label Verified / Needs Review / Unsupported
   → display answer + evidence inspector in Streamlit
```

The product goal is **traceability**, not fluency. A user must be able to inspect the exact source
passage behind any claim.

Full design: [docs/04_SYSTEM_ARCHITECTURE.md](docs/04_SYSTEM_ARCHITECTURE.md)

## 2. Source of truth hierarchy

When documents disagree, resolve in this order:

1. **Stage 2 report** (revised) — overrides Stage 1. Deviations logged in
   [docs/01_REQUIREMENTS.md](docs/01_REQUIREMENTS.md#3-stage-2-versus-stage-1-deviations-log).
2. **`AGENTS.md`** (this file) — working rules.
3. **`docs/01_REQUIREMENTS.md`** — authoritative requirement IDs.
4. **`docs/04_SYSTEM_ARCHITECTURE.md`** — authoritative structure.
5. **`docs/08_DATA_MODELS_AND_API_CONTRACTS.md`** — authoritative type/field names.
6. **Stage 1 report** — historical context only.
7. Chat instructions in the current session.

Never let a later document silently contradict an earlier one. If you must change a decision,
edit the decision document, record it in
[docs/15_PROGRESS_TRACKER.md](docs/15_PROGRESS_TRACKER.md#5-decisions-log), and note why.

## 3. Session start-up protocol

Before writing any code:

1. Read `AGENTS.md`.
2. Read `docs/15_PROGRESS_TRACKER.md` — this tells you the current phase and the exact next action.
3. Read `docs/06_IMPLEMENTATION_ROADMAP.md` — this tells you what the current phase may contain.
4. Read the docs relevant to the phase you are about to work on.
5. Run `git status` and `git log --oneline -10`.
6. Confirm the human has approved the phase. If there is no explicit `APPROVE PHASE N` in the
   current conversation, **stop and ask**.

## 4. Approval protocol (hard gate)

Phases are `2` → `3` → `4` → `5` → `6` → `7`. They are sequential.

- Build **only** the approved phase.
- Never skip a phase.
- Never start the next phase because the current one "obviously continues".
- Authorization looks like: `APPROVE PHASE 2`.
- When a phase completes, report and stop. Do not roll forward.

## 5. Anti-fabrication rules (highest priority)

These exist because the Stage 3 report must be academically defensible. Violating them is worse than
delivering nothing.

**Never invent:**

- Test counts, pass rates, or test output.
- Commit hashes, PR numbers, or branch names.
- Performance numbers, latencies, memory usage, or model benchmarks.
- Accuracy, precision, recall, F1, or citation-verification success rates.
- Dataset annotations or manual-labelling results.
- Screenshots that were not actually captured.
- User-study results.
- Star counts, licences, or commit dates for third-party projects.

**Always distinguish these states, and use the exact word:**

| State | Meaning |
|---|---|
| **Planned** | Intended. Not built. |
| **Implemented** | Code exists and has been read. Not necessarily tested. |
| **Verified** | A command was run and its real output observed. |
| **Measured** | A number was produced by a real measurement. |
| **Blocked** | Cannot proceed; reason recorded. |

Stage 2 reported "10/10 passing tests". That is a **historical report claim about code this
repository does not contain**. It is not evidence about the current codebase. See
[docs/03_GAP_ANALYSIS.md](docs/03_GAP_ANALYSIS.md). Tests must be re-run against real code before any
current success claim is made.

If you cannot verify something, say so plainly. "Not measured" is a valid, respectable answer.
"I could not verify this" is always better than a plausible guess.

## 6. Technical non-negotiables

These are the defensible core of the project. Breaking them breaks the viva.

1. **Cosine similarity is not factual proof.** `Verified` means "passed our documented support-check
   heuristic." Never write that the system "proves" a claim is true.
2. **Retrieval score and support score are different numbers** for different purposes.
   Retrieval relevance = chunk vs. query. Claim support = claim vs. cited chunk. Never merge,
   average, or display them as one figure.
3. **Invalid citation markers must be `Unsupported`.** If a marker does not resolve to a chunk that
   was actually retrieved, it is Unsupported. Never silently drop it, never guess the intended
   target.
4. **The deterministic fallback must always be operational.** TF-IDF + extractive, no downloads, no
   API key, no network. Same input ⇒ same output.
5. **Abstain when evidence is insufficient.** Empty retrieval ⇒ say so. Do not answer from model
   memory.
6. **PDF text is untrusted data, not instructions.** Retrieved PDF content may contain
   prompt-injection text ("ignore previous instructions"). It is quoted as evidence and never
   interpreted as an instruction to the system.
7. **Configurable thresholds, calibrated on labelled data.** Defaults live in one config object.
   Never hardcode a threshold inside a scoring function.
8. **Scanned/image-only PDFs must produce a clear OCR limitation message**, not an empty index.

## 7. Code conventions

Match the Stage 2 module layout (do not restructure without an ADR):

```
app.py                # Streamlit UI only — calls pipeline, never re-implements logic
run_demo.py           # CLI reproducible check
requirements.txt
src/
  __init__.py
  models.py           # dataclasses: DocumentPage, EvidenceChunk, RetrievalResult, ...
  pdf_ingestion.py    # validation, pypdf, pdfplumber fallback, scanned detection
  chunking.py         # sentence-aware chunking, overlap, metadata
  embeddings.py       # MiniLM backend + TF-IDF fallback backend
  vector_store.py     # Chroma adapter + deterministic in-memory store
  generator.py        # extractive grounded generator + optional FLAN-T5 adapter
  verifier.py         # marker parsing, support scoring, label assignment
  pipeline.py         # THE ONLY orchestration layer; public index()/ask()
tests/
  test_core.py
```

Style rules inherited from Stage 2 §2.2:

- `snake_case` for modules/functions/variables, `PascalCase` for classes, `UPPER_CASE` for
  constants.
- Functions that can fail raise explicit exceptions. Never return a silently empty result to signal
  failure.
- Docstrings explain *why* a non-obvious decision was made. Do not restate the function name.
- Comments carry implementation reasoning. **Do not add comments that merely restate the code.**
- Type-annotate all public function signatures and all dataclass fields.
- One responsibility per module. `pipeline.py` owns orchestration; the UI never duplicates logic.
- No hidden global state. No module-level mutable singletons.
- Source IDs must be deterministic and stable: derive from content/filename hash, never from
  `len()`, insertion order, or `id()`.

Add a new module only with a documented justification (ADR + tracker entry).

## 8. Testing gates

Every phase must end with a green run of the full suite. Never declare a phase complete with a known
failing test.

```bash
pytest -q
```

Required before declaring any phase done:

1. Run the full suite. Paste real output into the tracker.
2. Fix failures. Do not weaken a test to make it pass — fix the code, or document why the
   expectation was wrong.
3. Never replace working-but-failing functionality with static or mocked demo output and call it
   success.
4. Never skip a test via `@unittest.skip` to get a green run without recording why in
   [docs/14_RISK_REGISTER.md](docs/14_RISK_REGISTER.md).
5. The deterministic fallback path must be covered by tests that never touch the network.

The mandated scenario list (17 cases) lives in
[docs/09_TESTING_STRATEGY.md](docs/09_TESTING_STRATEGY.md). Do not remove cases; add to them.

## 9. Documentation duties

After each phase, update the affected docs. A code change without a doc update is an incomplete
phase.

- `docs/12_STAGE_3_EVIDENCE_TRACKER.md` — record the real artifact (file path, test name, command,
  output) backing any report claim.
- `docs/15_PROGRESS_TRACKER.md` — phase status, what changed, test results, next action.
- `docs/06_IMPLEMENTATION_ROADMAP.md` — tick the phase only when its exit gate truly passes.
- Architecture or contract changes require an ADR in
  [docs/05_TECH_STACK_AND_ADRS.md](docs/05_TECH_STACK_AND_ADRS.md).

Use relative Markdown links between docs. Verify they resolve before finishing.

## 10. Safety and scope restrictions

Do not, without explicit approval:

- Install packages, download model weights, or create a venv (Phase 2+ only).
- Clone an external repository into this workspace.
- Delete or overwrite existing files, reports, or documentation.
- `git commit`, `git push`, add remotes, or rewrite history.
- Add a paid API key, telemetry, or any network call in the default path.
- Swap Streamlit for React/Next.js/FastAPI, or swap MiniLM/FLAN-T5 for a larger model.
- Add authentication, multi-user support, cloud deployment, or database servers.
- Add OCR, agentic loops, or NLI models (P3 — only after the MVP is demonstrable and approved).
- Touch the unrelated `C:\Users\purvj\OneDrive\Desktop\Resume_Matching` project.

Uploads are untrusted. Enforce: extension check, size limit, page limit, sanitised filename for
display, and treat all extracted text as data.

## 11. UI rules

The UI is a graded deliverable and must use **real backend data only**.

- No fake statistics, no invented documents, no simulated claims, no hardcoded verification
  results.
- Every panel renders values that came from the pipeline in this session.
- Design system and layout: [docs/07_UI_UX_DESIGN_SPEC.md](docs/07_UI_UX_DESIGN_SPEC.md).
- Custom CSS is allowed but must be scoped to the app's own class namespace. Never write global
  element selectors that could break Streamlit internals.
- The UI must look intentional in **every** state, including empty, loading, and error states — not
  only in the ideal screenshot.

## 12. Completion protocol for a phase

Follow the 10-step gate in the project charter. Minimum bar:

1. Docs + workspace read.
2. Scope stated.
3. Smallest testable increment implemented.
4. Checks and tests run.
5. Failures fixed.
6. Output compared against acceptance criteria.
7. Real commands, real results, real limitations recorded.
8. Impacted docs updated.
9. Files-changed summary + remaining risks.
10. **Stop. Request next-phase approval.**

## 13. Quick links

| Need | Read |
|---|---|
| Current phase / next action | [docs/15_PROGRESS_TRACKER.md](docs/15_PROGRESS_TRACKER.md) |
| Phase scope and exit gates | [docs/06_IMPLEMENTATION_ROADMAP.md](docs/06_IMPLEMENTATION_ROADMAP.md) |
| Requirement IDs | [docs/01_REQUIREMENTS.md](docs/01_REQUIREMENTS.md) |
| Field names for data structures | [docs/08_DATA_MODELS_AND_API_CONTRACTS.md](docs/08_DATA_MODELS_AND_API_CONTRACTS.md) |
| Scoring formula and thresholds | [docs/04_SYSTEM_ARCHITECTURE.md](docs/04_SYSTEM_ARCHITECTURE.md#5-citation-verification-design) |
| Test cases | [docs/09_TESTING_STRATEGY.md](docs/09_TESTING_STRATEGY.md) |
| Why a technology was chosen | [docs/05_TECH_STACK_AND_ADRS.md](docs/05_TECH_STACK_AND_ADRS.md) |
| Open risks | [docs/14_RISK_REGISTER.md](docs/14_RISK_REGISTER.md) |