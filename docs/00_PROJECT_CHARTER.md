# 00 — Project Charter

**Status:** Approved baseline · Last updated 2026-10-08
**Related:** [README](../README.md) · [Requirements](01_REQUIREMENTS.md) · [Roadmap](06_IMPLEMENTATION_ROADMAP.md) · [Risk Register](14_RISK_REGISTER.md)

---

## 1. Problem statement

Generative AI assistants produce confident, well-formatted academic answers whose citations are
frequently unverifiable. A student cannot tell a real source from a plausible-looking fabricated one
without manually opening and reading every reference — hours of work per assignment. Stage 1 of this
project documented this problem and cited Athaluri et al. (Cureus, 2023) for fabricated DOIs and
titles in AI-generated scientific writing.

The gap Stage 1 identified: **there is no lightweight tool that both retrieves the user's own
papers and verifies that the claims in the generated answer are actually present in the retrieved
text.**

## 2. Purpose

Build a local application that answers a question from the user's own academic PDFs, cites the exact
file and page for every claim, and then independently checks whether the cited passage supports the
claim — labelling each claim `Verified`, `Needs Review`, or `Unsupported`, with the evidence and the
score visible.

## 3. Scope

### In scope (committed)

| # | Capability |
|---|---|
| S1 | Multi-PDF upload with validation (extension, size, encryption, empty content) |
| S2 | Page-wise text extraction: `pypdf` primary, `pdfplumber` fallback |
| S3 | Sentence-aware chunking, ~180 words / 30-word overlap, configurable |
| S4 | Semantic embedding with `all-MiniLM-L6-v2` |
| S5 | Local persistent vector storage in Chroma |
| S6 | Top-k retrieval with stable source mapping |
| S7 | Grounded answer generation, optional local `google/flan-t5-small` |
| S8 | Deterministic TF-IDF + extractive fallback with zero downloads |
| S9 | Resolvable citation markers `[S1, p.5]` |
| S10 | Per-claim verification against cited evidence with visible score |
| S11 | Three-state verification labels + abstention |
| S12 | Evidence inspector showing file, page, passage, score, explanation |
| S13 | Premium Streamlit UI covering every activity and error state |
| S14 | Automated test suite covering 17 mandated scenarios |
| S15 | Reproducible CLI demo (`run_demo.py`) |

### Out of scope (explicitly excluded)

Live academic scraping (arXiv/Scopus/DBLP) · paid APIs (OpenAI, Anthropic, Gemini, Groq) ·
authentication · multi-user collaboration · cloud deployment · database servers · mobile app ·
non-English papers · reference-manager integration (Zotero) · OCR · agentic/multi-agent workflows ·
NLI-based verification · multi-turn conversational memory.

These exclusions come from Stage 1 §1.3 and Stage 2, and are restated so a future agent does not
helpfully "improve" the project out of scope.

**50 PDFs is a configurable operating target, not a performance guarantee.** See
[R-08](01_REQUIREMENTS.md#2-functional-requirements).

## 4. Constraints

| ID | Constraint | Source |
|---|---|---|
| C1 | Zero paid APIs in the default and demo path | Stage 2 §3.1 |
| C2 | No GPU requirement; must run CPU-only on an ordinary 8 GB laptop | Stage 2 §3.2 |
| C3 | Fully offline-capable fallback path | Stage 2 §1.1 |
| C4 | Python 3.10+, one pinned version across the team | Stage 2 §3.2 |
| C5 | 3–5 focused development days; team has concurrent SIH obligations | Project brief |
| C6 | Streamlit is the UI; no React/Next.js/FastAPI swap without approval | Project brief |
| C7 | No LangChain | Stage 2 §3.1 (Table 4) |
| C8 | Stage 3 report must match actual code | Academic integrity |

## 5. Success criteria

### 5.1 Functional success (MVP gate)

1. A user uploads ≥1 PDF and the system reports real page counts.
2. A user asks a question and receives an answer whose every factual sentence carries a citation.
3. Every citation marker resolves to a real filename and real page number.
4. Every claim receives one of the three labels, with its score visible.
5. Selecting a citation reveals the exact retrieved passage.
6. When retrieval returns nothing relevant, the system says so instead of answering.
7. The whole workflow runs with **no internet connection and no API key** via the fallback profile.

### 5.2 Evidence success (Stage 3 gate)

Every quantitative claim in the Stage 3 report maps to an artifact in
[12_STAGE_3_EVIDENCE_TRACKER.md](12_STAGE_3_EVIDENCE_TRACKER.md): a file path, a test name, a
command with its real output, or a measurement procedure that someone else can re-run.

### 5.3 Academic-defence success

Any team member can explain, unaided: why chunk size is 180 words; why retrieval score ≠ support
score; why low similarity ≠ hallucination; why cosine similarity is not proof; what the fallback
buys us; and what the system cannot do.

## 6. Definition of done per phase

A phase is done when **all** hold:

- [ ] Every requirement tagged to that phase in [01_REQUIREMENTS.md](01_REQUIREMENTS.md) is implemented.
- [ ] `pytest -q` passes with real, pasted output.
- [ ] The phase exit gate in [06_IMPLEMENTATION_ROADMAP.md](06_IMPLEMENTATION_ROADMAP.md) is met.
- [ ] Impacted docs updated, including the evidence tracker and progress tracker.
- [ ] Remaining risks re-stated honestly.
- [ ] Next-phase approval requested — and the agent has stopped.

## 7. Stakeholders and roles

| Person | Role | Accountable for |
|---|---|---|
| Rishabh Jain | Citation verification owner | `src/verifier.py`, thresholds, calibration, architecture review |
| Purv Jain | Pipeline + UI owner | `src/pipeline.py`, retrieval, `app.py`, integration demo |
| Bhavya Soni | Ingestion + QA owner | `src/pdf_ingestion.py`, tests, fixtures, docs, evidence tracking |
| Prof. Priyanka Kharatmol | Project guide | Academic sign-off |
| All three | Shared understanding | Every member can explain the whole pipeline |

Ownership establishes accountability, not knowledge silos — Stage 2 §5.1 says this explicitly.

## 8. Guiding principles

1. **Traceability over fluency.** A boring answer with perfect citations beats a brilliant answer
   with unverifiable ones.
2. **Honesty over impressive numbers.** "Not measured" beats a plausible invented figure.
3. **Simplicity over completeness.** A working vertical slice beats a broad half-finished one.
4. **Fallback before features.** The deterministic path must work before any model is downloaded.
5. **Explainable over clever.** A score a student can recompute by hand is worth more than a black
   box.

## 9. Change control

Any change to §3 scope, §4 constraints, or the verification formula requires:

1. An ADR in [05_TECH_STACK_AND_ADRS.md](05_TECH_STACK_AND_ADRS.md) (or an architecture amendment in
   [04_SYSTEM_ARCHITECTURE.md](04_SYSTEM_ARCHITECTURE.md)).
2. An entry in the [deviations log](01_REQUIREMENTS.md#3-stage-2-versus-stage-1-deviations-log) if it
   touches a Stage 2 decision.
3. A [risk register](14_RISK_REGISTER.md) update.
4. An entry in the [decisions log](15_PROGRESS_TRACKER.md#5-decisions-log).

Minor, reversible implementation choices do not need all four — use judgement and record them in the
progress tracker.