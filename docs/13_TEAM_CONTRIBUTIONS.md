# 13 — Team Contributions

**Status:** Phase 7 baseline · Last updated 2026-10-08 · **Two commits exist; the Phases 0–6 one carries a placeholder author** (B-05)
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

## 5. Verified contributions

### 5.1 What the commit history actually shows

A repository now exists. Two commits:

| Commit | Author | Scope |
|---|---|---|
| `fd2be70` | `Purv-Jain <purv.jain24@sakec.ac.in>` | Phase 7 ? Stage 3 report draft, reproducible logs, five verifier defects fixed |
| `9772226` | `Your Name <your.email@example.com>` | Phases 0?6 ? the entire implementation |

```bash
git log --pretty=format:"%h %an <%ae> %ad %s" --date=short
git shortlog -sne --all
```

`9772226` was authored with the **git default placeholder identity** ? the repository was created
before a name and email were configured. It contains every line of production code and all but the
most recent tests. **It cannot be decomposed into per-member contributions**, and no table derived
from it would be anything but invention.

### 5.2 The decision, and why disclosure beat a rewrite

Rewriting `9772226` to attach the correct author was considered and **rejected**:

- it changes a commit already pushed to a **public** repository;
- it invalidates that commit for anyone who has cloned it;
- it needs both teammates to coordinate mid-project;
- and it buys tidiness, not accuracy ? the placeholder author is a documentation defect, not
  misconduct, so the remedy would cost more in trust than the defect does.

**Chosen: disclose.** The placeholder is visible in the log, stated in report
[?13](16_STAGE_3_REPORT_DRAFT.md#13-individual-contributions), and tracked as **B-05**. Correcting
it properly is post-submission work, when a rewrite is cheap because nothing depends on it.

### 5.3 File-level attribution, and its limits

This is **not** commit authorship and must never be presented as such. It records who authored which
file in this workspace, and for Phases 4?6 it is partly reconstruction:

| Member | Files attributed in this workspace | Commits |
|---|---|---|
| Rishabh Jain | `src/verifier.py`, `tests/test_verification.py` ? **which lines were written by which person is not recorded anywhere reliable** | `9772226` only (placeholder author) |
| Purv Jain | `src/models.py`, `src/__init__.py`, `src/embeddings.py`, `src/vector_store.py`, `src/pipeline.py`, `src/generator.py`, `app.py`, `run_demo.py`, `conftest.py`, `requirements.txt`, `pytest.ini` | `fd2be70`, `9772226` |
| Bhavya Soni | `src/pdf_ingestion.py`, `src/chunking.py`, `tests/conftest.py`, `tests/test_core.py`, `tests/test_hardening.py`, `tools/*.py`, `.github/workflows/tests.yml` | `9772226` only (placeholder author) |

### 5.4 The statement this table cannot make

Phases 4 to 6 were largely executed by **one AI agent** working from these documents, on the team's
direction. Attributing lines to a named student without a commit to prove it would be the fabrication
this document exists to prevent ? so nothing stronger than the above is claimed, and the conclusion a
reader should draw is that **the per-member split is not established by the available evidence**.

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
