# 13 — Team Contributions

**Status:** Phase 3 baseline · Last updated 2026-10-08 · **No commits exist — the workspace is not yet a git repository**
**Related:** [Charter §7](00_PROJECT_CHARTER.md#7-stakeholders-and-roles) · [Evidence Tracker §11](12_STAGE_3_EVIDENCE_TRACKER.md#11-contribution-evidence) · [Roadmap](06_IMPLEMENTATION_ROADMAP.md)

---

## 1. The rule this document exists to enforce

**Planned ≠ actual.** Two separate tables, never merged:

- **§3 Planned ownership** — intention, from Stage 2 §5.1. Valid for *assigning work*.
- **§5 Verified contributions** — what Git history and file authorship actually show. Valid for the
  Stage 3 report.

Stage 2 §6.1 said its commit IDs "must not be presented as evidence of an individual's work", and
§5.2 said "No invented contribution percentages, PR numbers or commit hashes." Those were correct and
this document enforces them mechanically.

> **Forbidden in the Stage 3 report:** invented percentages ("Rishabh did 40%"), invented PR numbers,
> invented commit hashes, and any contribution claim not backed by `git log --author=`.

## 2. Team

| Member | PRN | Primary ownership | Review focus |
|---|---|---|---|
| Rishabh Jain | 124BTCM1054 | Citation verification | Architecture |
| Purv Jain | 124BTCM1171 | Pipeline + retrieval + UI | Integration |
| Bhavya Soni | 124BTCM1215 | Ingestion + tests + docs | Test coverage |

Project guide: Prof. Priyanka Kharatmol.

## 3. Planned ownership (Stage 3)

Inherited from Stage 2 §5.1 and mapped onto this roadmap.

### 3.1 Rishabh Jain — citation verification

| Phase | Planned artifacts |
|---|---|
| 2 | Review chunk size choice against MiniLM's `max_seq_length`; review `DocumentPage`/`EvidenceChunk` fields |
| 3 | Review `RetrievalResult` shape and enforce the retrieval/support separation |
| 4 | **Own** `src/verifier.py`; `VerificationConfig`; token-overlap; contradiction and numeric checks; label assignment; reason codes |
| 4 | Own the EC-09→EC-12 verification tests |
| 6 | Own the ≥20-case labelling set and threshold calibration; produce the precision/recall/F1 and false-`Verified` rate |
| all | Architecture review at every gate |
| 7 | Lead on "Verification design and its stated limits" in the report |

**Explains:** why 180/30 chunk size, what cosine similarity measures, why `Needs Review` exists, why
an unresolvable marker is `Unsupported`, how token overlap and contradiction checks work, why the
threshold is calibrated rather than fixed.

### 3.2 Purv Jain — pipeline, retrieval, UI

| Phase | Planned artifacts |
|---|---|
| 2 | `src/models.py`; `ChunkConfig`; chunking wiring |
| 3 | Own `src/embeddings.py` and `src/vector_store.py`; TF-IDF backend; in-memory store; Chroma adapter; retrieval + top-k clamping |
| 4 | Own `src/generator.py` (extractive + FLAN-T5 adapter); `pipeline.py` orchestration; abstention |
| 5 | Own `app.py` and the design implementation; all six surfaces; all 17 states |
| 6 | `run_demo.py`; latency/RAM measurement |
| 7 | Lead on "Implementation" and "UI/UX" in the report |

**Explains:** how the pipeline is orchestrated, how retrieval works and why, how the extractive
generator works, how Streamlit state and caching are managed, why FLAN-T5 is optional.

### 3.3 Bhavya Soni — ingestion, testing, documentation

| Phase | Planned artifacts |
|---|---|
| 2 | Own `src/pdf_ingestion.py`: validation, pypdf, pdfplumber fallback, scanned detection, sanitisation, stable IDs |
| 2 | Test fixtures (synthetic valid/encrypted/scanned/corrupt PDFs) |
| 3 | `requirements.txt` pinning; clean-venv verification; CI workflow |
| 6 | Own the full test suite; EC-01→EC-17 coverage; security tests; offline run |
| all | Docs, evidence tracker, progress tracker |
| 7 | Lead on "Testing" and the evidence appendix |

**Explains:** why `pypdf` first and `pdfplumber` second, how encryption is detected, why a scanned
PDF cannot be handled, how stable source IDs are derived, why each edge case is tested.

### 3.4 Shared

Per Stage 2 §5.1: *"Ownership is used to establish accountability, not to create isolated knowledge."*

Every member must be able to explain every module. See
[11 §4.4](11_DEMO_AND_VIVA_PREPARATION.md#44-demonstrable-technical-understanding) for the
15-point shared list.

Phase 2 planning, Phase 6 metrics, and the Phase 7 report are explicitly **all-members** work.

## 4. Cross-review matrix

No feature merges without a second reader.

| Phase | Primary | Reviewer |
|---|---|---|
| 2 | Bhavya (ingestion) / Purv (models) | Rishabh + each other |
| 3 | Purv | Rishabh |
| 4 | Rishabh (verifier) / Purv (generator) | Each other |
| 5 | Purv | Bhavya (states), Rishabh (verification panel) |
| 6 | Bhavya | All |
| 7 | All | All |

## 5. Verified contributions (TO BE FILLED FROM GIT)

**Still empty after Phase 6 — and not because nothing was written, because there is nothing to
read.** `git status` in this directory returns `fatal: not a git repository`. Phases 2 to 6 produced
nine source modules, a five-file test suite of **402 passing tests**, four CLI/measurement tools and
the full document set, and **none of it is under version control** (blocker **B-05** in
[15_PROGRESS_TRACKER.md §6](15_PROGRESS_TRACKER.md#6-blockers)).

This is a real risk to the Stage 3 submission, not a formality: the report's contribution table must
be assembled from `git log --author=`, and right now that command has no output to give. Creating the
repository needs a human decision about remotes and authorship. Phase 7 item 7.4 cannot start
without it.

Until then, the only honest record is **file authorship in this workspace**, and file authorship is
not commit authorship:

| Member | Files attributed in this workspace | Commits (real hash + subject + date) | Status |
|---|---|---|---|
| Rishabh Jain | `src/verifier.py`, `tests/test_verification.py` — **which lines were written by which person is not recorded anywhere reliable** | _none yet_ | IMPLEMENTED, uncommitted |
| Purv Jain | `src/models.py`, `src/__init__.py`, `src/embeddings.py`, `src/vector_store.py`, `src/pipeline.py`, `src/generator.py`, `app.py`, `run_demo.py`, `conftest.py`, `requirements.txt`, `pytest.ini` | _none yet_ | IMPLEMENTED, uncommitted |
| Bhavya Soni | `src/pdf_ingestion.py`, `src/chunking.py`, `tests/conftest.py`, `tests/test_core.py`, `tests/test_hardening.py`, `tools/build_cases.py`, `tools/evaluate.py`, `tools/measure.py`, `.github/workflows/tests.yml` | _none yet_ | IMPLEMENTED, uncommitted |

**The statement this table cannot make.** Phases 4 to 6 were largely executed by one AI agent working
from these documents. Attributing lines to a named student without a commit to prove it would be the
fabrication this document exists to prevent, so the column above is labelled "attributed in this
workspace" and nothing stronger. When the repository exists, Phase 7 must reconcile this against real
`git log` output and correct it if the two disagree.

Procedure once a repository exists:

```bash
git log --author="Rishabh" --pretty=format:"%h %ad %s" --date=short
git log --author="Purv"    --pretty=format:"%h %ad %s" --date=short
git log --author="Bhavya"  --pretty=format:"%h %ad %s" --date=short
git shortlog -sne --all
```

| Member | Commits (real hash + subject + date) | Files materially authored | Tests owned | Review given | Status |
|---|---|---|---|---|---|
| Rishabh Jain | _none yet_ | _none yet_ | _none yet_ | _none yet_ | PLANNED |
| Purv Jain | _none yet_ | _none yet_ | _none yet_ | _none yet_ | PLANNED |
| Bhavya Soni | _none yet_ | _none yet_ | _none yet_ | _none yet_ | PLANNED |

### 5.1 What counts as evidence of contribution

| Counts | Does not count |
|---|---|
| Commits authored by the person's own Git account | Commits that existed before Stage 3 (Stage 2's four hashes) |
| Substantive changes to a module they own | A one-line whitespace fix |
| Tests that fail without their change | Tests copied from a teammate unchanged |
| A written review that changed a decision | Being listed in a RACI table |
| Documented design decisions they authored | Being named as a team |

### 5.2 Branch and commit conventions

Adopted from Stage 2 §3.3:

| Convention | Value |
|---|---|
| Branches | `main`, `feature/ingestion`, `feature/chunking`, `feature/retrieval`, `feature/verifier`, `feature/ui`, `feature/tests`, `docs/*` |
| `main` invariant | Only code that passes the current test suite |
| Merge rule | Owner runs tests → another member reviews → merge |
| Commit format | Conventional prefixes: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:` |
| Conflict rule | Compare *intended behaviour*, re-run tests after merge. Never blind "ours/theirs" |

Branch → ownership mapping:

| Branch | Owner |
|---|---|
| `feature/ingestion`, `feature/chunking` | Bhavya |
| `feature/embeddings`, `feature/store`, `feature/pipeline`, `feature/ui` | Purv |
| `feature/verifier`, `feature/evaluation` | Rishabh |
| `feature/tests`, `feature/ci` | Bhavya |
| `docs/*` | whoever authored the content; Bhavya integrates |

## 6. Timeline of contribution (to be recorded)

| Date | Member | Action | Commit |
|---|---|---|---|
| 2026-10-08 | All | Phase 0 research + Phase 1 documentation | _pending first commit_ |
| 2026-10-08 | — | Phase 2: models, ingestion, chunking, 56 passing tests | _pending first commit_ |
| 2026-10-08 | — | Phase 3: embeddings, vector stores, pipeline, 144 passing tests | _pending first commit_ |

## 7. Deviations from Stage 2 ownership

None recorded. Any future change must be logged here with a reason.

| # | Stage 2 said | Now | Reason | Date |
|---|---|---|---|---|
| — | — | — | — | — |

## 8. Pre-submission check

- [ ] A git repository exists and every Phase 0–7 change is committed (**currently failing** — B-05)
- [ ] Every commit in §5 was authored by the account it is attributed to
- [ ] No commit hash appears in the report that is absent from §5
- [ ] No invented percentages, PR numbers, or issue links
- [ ] Each member has personally run the full test suite and the demo
- [ ] Each member can answer [11 §4.4](11_DEMO_AND_VIVA_PREPARATION.md#44-demonstrable-technical-understanding) unaided
- [ ] Stage 2's four commit hashes are **not** presented as anyone's Stage 3 work
- [ ] The report describes contribution by artifact, not by percentage
- [ ] Evidence tracker §11 matches this document exactly