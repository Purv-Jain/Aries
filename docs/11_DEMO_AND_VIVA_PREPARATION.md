# 11 — Demo & Viva Preparation

**Status:** Phase 7 rehearsal-ready · Last updated 2026-10-08
**Related:** [Evidence Tracker](12_STAGE_3_EVIDENCE_TRACKER.md) · [Team Contributions](13_TEAM_CONTRIBUTIONS.md) · [Evaluation](10_EVALUATION_METRICS.md)

---

## 1. Demo philosophy

**The demo proves the evidence chain works. It does not prove the system is smart.**

Show the examiner the boring, powerful thing: a claim, its marker, the actual page text, and the
score. If the demo is a series of lucky correct answers, it proves nothing. If it is one answer
followed by "here is the exact passage, here is the score, here is what that label does not mean" —
that is the project.

### 1.1 Rules

| Rule | Reason |
|---|---|
| Demo the **offline** profile first | Proves the zero-cost, no-API-key promise before anything else |
| Every screenshot is either captured or labelled schematic | Stage 2 set this precedent (§2.3) and it was the right call |
| No rehearsed miracle outputs | If it needs a magic incantation, it isn't a demo, it's a story |
| Have a **failure** ready | Showing an honest `Unsupported`/`abstention` is more convincing than a lucky hit |
| Never say "verified" alone | Always "passed our support check" ([ADR-0006](05_TECH_STACK_AND_ADRS.md#adr-0006--never-describe-cosine-similarity-as-proof)) |

## 2. Demo script

Target duration: **6–8 minutes**. Pre-stage the PDF so upload time does not eat the clock, but have a
cold run ready if asked.

### Beat 1 — The problem (45 s)

> "Large language models confidently cite papers that do not exist. Athaluri et al. documented
> fabricated DOIs in AI-generated scientific writing. The problem is that a student cannot tell a real
> citation from a plausible fake one without opening every source. Our system makes every claim in an
> answer traceable to a page, and then checks whether that page actually supports the claim."

### Beat 2 — Index a real PDF (60 s)

Upload the Stage 1 or Stage 2 report. Show:
- document library row: real filename, **measured** page count, measured chunk count
- dashboard stat tiles updating from the live index
- the backend badge (`Lexical / in-memory` or `MiniLM / Chroma`)

Say: *"Page count is measured, not declared. That distinction is the whole project."*

### Beat 3 — Ask a question, show the chain (90 s)

Ask a question with an unambiguous answer in the document — e.g. *"Why did we choose Chroma for vector
storage?"* or *"How large is the chunk size and why?"*

Walk through in this order:
1. Answer text with inline `[S1, p.9]` markers
2. Verification summary: **counts**, and the worst score — not an average
3. Click the marker → **Evidence inspector**: filename, `page N of M`, the verbatim passage in mono,
   support score broken into `similarity` and `overlap`, and separately the retrieval relevance score
4. Read the explanation aloud, including its final sentence: *"…this indicates correspondence, not
   formal entailment."*

**This is the beat that matters.** Pause here.

### Beat 4 — Show the refusal, and be honest about its edge (120 s)

> **Changed twice in Phase 7.** This beat originally promised an abstention the system did not
> perform, was corrected to *demonstrate the failure*, and is now correct again because the failure
> was fixed ([R-24](14_RISK_REGISTER.md)). Ask about mercury's boiling point: the system refuses,
> names the query terms that failed to match, and shows the passages it considered.

| # | Action | Expected | Why it lands |
|---|---|---|---|
| 1 | Ask a question the documents **do** answer | claims with `[Sx, p.y]`, per-claim labels | the working case |
| 2 | Show a claim the source contradicts | `Unsupported` with `contradiction_detected` | it caught a polarity error |
| 3 | Show a deliberately broken marker `[S7, p.1]` | `Unsupported`, `unresolvable_reference` | a citation pointing nowhere is caught |
| 4 | **Ask about mercury's boiling point** | it **refuses**, naming `boiling`, `mercury`, `point`, `sea` as unmatched | the failure mode is now closed, on screen |
| 5 | Ask *"What is the inference throughput of MiniLM on this laptop?"* | **it answers** — and that is correct to disclose | shows the gate's real limit, volunteered |

On step 4:

> "It refused, and it told me *why*: none of `boiling`, `mercury`, `point` or `sea` appears in any
> passage it retrieved. That check runs before the generator, so no claim is built and then labelled
> ‘unsupported’ afterwards. It refuses 18 of 24 out-of-corpus questions with no false refusals on 24
> answerable ones, and the threshold came from a sweep over 48 hand-labelled questions."

On step 5 — **say this before they find it**:

> "This one it gets wrong. MiniLM and 'laptop' both appear in the report, so the vocabulary matches,
> but the report never states a throughput. A lexical check cannot tell 'the words are here' from
> 'the answer is here'. Those six cases are in our labelled set precisely so we cannot quote a
> better number by leaving them out. Closing that gap needs entailment, not a better threshold."

Beat 4 is worth more than three successful answers. Volunteering the case your system still gets
wrong, with the reason it is the wrong shape of fix, is the difference between a demo and a
defence.

### Beat 5 — Show the offline guarantee (60 s)

> "This entire run used TF-IDF and an extractive generator. No GPU, no API key, and — here — no
> internet."

Support it with a number rather than an assurance: 402 tests pass with `socket.connect` replaced by
a function that raises, then a full index → ask → verify cycle run to completion
([logs/02](../logs/02_test_suite_offline.txt)). The offline path is not permitted to try the network.

**Do not toggle the semantic profile live.** There are no MiniLM or FLAN-T5 weights on this machine,
so the toggle would attempt a download and fail on stage. If asked, say the semantic paths are
written and their *degradation* behaviour is tested, but their success paths are unmeasured — and
that is exactly why the offline profile is the default ([ADR-0011](05_TECH_STACK_AND_ADRS.md#adr-0011--optional-flan-t5-small-not-required)).

### Beat 6 — Close on the limitation (30 s)

> "The honest limit: `Verified` means the claim passed our support heuristic — a weighted combination
> of semantic similarity and token overlap. It is not logical entailment, and it is not proof. Proving
> that would need an NLI model, which is our documented next step."

Ending on the limitation makes everything before it more credible.

## 3. Demonstration checklist

- [ ] Fixture PDF staged, and a **second** PDF for the multi-document case
- [ ] Internet **off** for the offline-profile beats
- [ ] Two questions memorised: one clearly absent (**it will refuse** — mercury's boiling point) and one adversarial (**it will answer, wrongly** — MiniLM throughput). Rehearsing only the first is how you get caught
- [ ] A known-contradiction case memorised
- [ ] Screenshots of every state, each labelled *captured* with its timestamp — **none exist yet (7.2)**
- [ ] `logs/02_test_suite_offline.txt` open in a tab, in case "how do you know?" comes early
- [ ] `pytest -q` output on screen, real, not from memory
- [ ] `run_demo.py` ready as a fallback if the browser misbehaves
- [ ] Demo re-run end-to-end **twice** before presenting
- [ ] Any slide showing a number has that number in the evidence tracker

## 4. Viva preparation

### 4.1 Stage 2 questions (carry forward, with updated answers)

| Question | Answer | Why it is asked |
|---|---|---|
| Why RAG instead of asking an LLM directly? | RAG supplies evidence at query time, so the answer can be traced to retrieved passages. Traceability is this project's entire objective. | Core motivation |
| Why was chunk size changed from Stage 1? | Stage 1 mixed tokens and words, and proposed chunks larger than MiniLM's effective input length. `all-MiniLM-L6-v2` has `max_seq_length = 256` (verified via the HF API), so a 500-token chunk is truncated by about half and the embedding then represents only part of the evidence. ~180 words ≈ 230–240 word-pieces, which fits. | Tests whether you understand a model constraint or just picked a number |
| Is cosine similarity proof that a citation is correct? | No. It measures relatedness in an embedding space. That is why there are configurable thresholds, a `Needs Review` band, and an explicit statement that `Verified` is not entailment. | **The most likely deep question.** Do not bluff |
| Why not call every low score a hallucination? | Low scores also come from paraphrasing, poor extraction, or bad chunking. `Unsupported` is a description of what our system measured; *hallucination* is an interpretation that needs its own evaluation. | Tests scientific caution |
| Why Chroma? | It persists embeddings and metadata locally and needs no separately managed database server at this scale. | Dependency justification |
| Why keep a TF-IDF fallback? | Deterministic testing with no model weights, and the demo works with no network and no key. It is what makes the offline guarantee testable rather than aspirational. | Architecture reasoning |
| Why FLAN-T5-small? | Compact and instruction-tuned, runnable locally. Trade-off: weaker generation and slower on CPU. It is optional because a verifiable answer beats a fluent one. | Trade-off reasoning |
| What is the difference between retrieval score and verification score? | Retrieval ranks passages against the question. Verification compares a claim with the passage it cites. Different questions; they are never averaged or substituted. | Core concept |
| What happens with a scanned PDF? | `pypdf`/`pdfplumber` cannot read image-only text. The system says OCR is needed and that it is out of scope. | Limitation awareness |
| What would the next technical improvement be? | Build the manually labelled claim/evidence set, calibrate thresholds on it, then compare our similarity verifier against a small NLI or cross-encoder verifier. | Self-awareness |

### 4.2 New questions Phase 3/4 will invite

| Question | Answer |
|---|---|
| Why is your evaluation set self-authored? What is the bias? | Yes — the questions were written by the same people who wrote the chunker, so the absolute numbers are optimistic. The report states this. The mitigation is that questions include unanswerable ones and negative cases, and we report counts and the false-`Verified` rate rather than a flattering average. |
| How do you know "20 cases" is enough? | It isn't, statistically. It is enough to demonstrate the method and calibrate a two-threshold heuristic, and the report states the sample size and the limitation. A larger set is the next step. |
| Why 0.7 and 0.3? | They are Stage 2's stated formula. 0.7 weights semantic similarity as the stronger signal, 0.3 adds a lexical check that catches cases where embeddings are close but the actual words are absent. They are configuration, and the report shows the calibration sensitivity. |
| Is `token_overlap` Jaccard? | No — containment. A claim is a short summary of a long passage; Jaccard punishes that asymmetry and under-scores correct citations. The trade-off is that containment can be inflated by a chunk containing the words while contradicting them, which is why the contradiction check exists. |
| Can someone inject instructions through a PDF? | Yes, and we treat PDF text as untrusted data. The extractive generator selects existing sentences and cannot obey instructions found in evidence; markers are only ever taken from the retrieved set; and any marker that does not resolve is marked `Unsupported`. So the worst case is a visible failure, never a false `Verified`. We have a test for it. |
| Why is your answer not fluent? | Deliberate. Abstractive generation can introduce wording absent from the evidence — the exact failure we exist to detect. A verifiable answer that reads like a citation is more useful here than a fluent one. |
| Did you reuse anyone else's code? | No third-party source was copied. We use Apache-2.0/BSD/MIT libraries as dependencies. We did study several projects and re-implemented their patterns, cited in the report — including one whose licence (`NOASSERTION`) means we could not use its code at all. That decision is documented in our ADR. |
| Stage 2 said 10/10 tests passed. How many now? | Our own number, from our own run, with the output in the report. Stage 2's prototype is not in this repository, so we re-implemented and re-measured rather than inheriting the figure. |
| What is the biggest limitation? | The verifier is a similarity heuristic, not entailment. A claim can share vocabulary and polarity cues with a passage while still being wrong in a way we cannot detect. NLI is the documented next step. |

### 4.3 Traps — do not fall into these

| Trap | Why it is tempting | The right move |
|---|---|---|
| Implying `Verified` = true | It sounds like the result you promised | Say "passed the support check" and add the caveat |
| Quoting a third party's benchmark as yours | It would look impressive | Attribute it; note it was not reproduced |
| Claiming a 50-PDF capacity | Stage 1 said 50 | "A configurable operating target. Here is what we actually measured." |
| Blaming a low score on hallucination | It sounds decisive | "Unsupported describes our measurement; hallucination is a separate claim needing evaluation." |
| Defending Stage 2's 10/10 as your own | It is already written down | Re-run, report your number |
| Claiming prompt-injection defence is complete | It is a mitigations story | Name the controls and the residual risk honestly |
| Overstating accuracy from 20 cases | 20 cases invites percentage claims | Give counts, sample size, and the bias |
| Admitting a low score to look modest | Feels safer | Report it accurately with the reason |
| **Presenting the 0.958 "agreement" as two independent labellers** | It reads as a rigorous inter-annotator study | It was a self-reconciliation by the same agent that wrote the verifier. Say so; it costs nothing and is checkable |
| **Quoting precision 1.000 as "the system never makes a mistake"** | 1.000 is the number examiners remember | It is 1.000 on 24 self-authored cases. The honest sentence: "on this labelled set, at this threshold" |
| **Quoting 0.750 as "it knows when it doesn't know"** | The number sounds finished | "0.750 correct on 48 hand-labelled questions, 0.000 false. It was 0.000 before Phase 7. Six adversarial cases still get confident answers, and here they are." |
| Claiming CI is green without the run ID | It would sound rigorous | It is green — run 37880879892, all three jobs. Say the number; it is checkable. |
| Claiming the UI was visually verified | 98 UI tests sound like coverage | They prove the render path executes, not that a layout is readable |

### 4.5 The three questions Phase 6 made newly answerable

These now have measured answers. Use them.

**"How do you know 0.63 is the right threshold?"**
Sweep 0.30 → 0.90 over a 24-case labelled set from our own 15-page report. 0.63 is the
highest-F1 point with false-`Verified` = 0.000 (P 1.000, R 0.800, F1 0.889). The previous 0.62
was inherited from Stage 2 unmeasured and carries a false-`Verified` rate of 0.125. Full sweep:
`logs/05_evaluate.txt`.

**"Did your own testing find real bugs?"**
Yes — the unit suite found nothing, and the evaluation found two. The negation check compared one
sentence against a whole 180-word chunk, so six correct claims returned `contradiction_detected`
because the chunk contained "not an OCR engine" elsewhere. And it compared negation *cue words*
rather than *polarity*, so "does not depend" and "no … required" read as opposites. Accuracy over
the 24 cases went 0.292 → 0.625 → 0.667. Both are regression-tested now. Saying this costs nothing
and demonstrates the evaluation was worth running.

**"What is the system's worst failure?"**
Answer the *current* one, then volunteer the one you fixed, because both are true and only the
second is impressive if you volunteer it.

**Worst failure, now:** adversarial abstention misses. Ask "What is the inference throughput of
MiniLM on this laptop?" — MiniLM and laptop are both in the report, so coverage passes, and the system
answers with a confident citation to a passage that never states a throughput. Six of 24 labelled
unanswerable questions are like this; we measure **0.750** correct abstention overall, 1.000 on
clearly-out-of-domain questions and **0.000** on these. A lexical pre-generation check cannot tell
"the words are here" from "the answer is here". Closing it needs entailment, not a better threshold.

**Worst failure, found and fixed:** abstention did not work at all. It measured **0.000**, and across
10 out-of-corpus questions it emitted 50 claims of which **15 were labelled `Verified`** — about
photosynthesis and the northern lights. The generator's only trigger asked "is any sentence relevant
enough?" and never "do these passages answer the question?". We first tried the obvious fix, a floor
on the cosine relevance score, **measured that it cannot work** (answerable 0.138–0.257 overlaps
unanswerable 0.072–0.192), and switched to coverage of the question's content words, swept over 48
hand-labelled questions. Naming the rejected fix is the part that lands.

### 4.4 Demonstrable technical understanding

Every member should be able to explain, unaided:

1. Why `all-MiniLM-L6-v2` and what `max_seq_length = 256` implies for chunk size.
2. What TF-IDF does and why it is a legitimate retrieval fallback rather than a cop-out.
3. What cosine similarity measures and what it does not.
4. How token overlap is computed and why containment beats Jaccard here.
5. Why retrieval and support scores must stay separate.
6. Why an unresolvable marker is `Unsupported` instead of being repaired.
7. Why the extractive generator is the default.
8. How stable source IDs are derived and why `id()` or index-based IDs would break citations.
9. Why Chroma is optional and what happens when it is unavailable.
10. What "abstain" means and why it is a feature.
11. What the contradictory and numeric checks catch that low similarity does not.
12. How the system would be attacked via a prompt injection in a PDF, and what limits the damage.
13. Why Stage 2 overrode Stage 1 on chunk size, labels, and `PyPDF2`.
14. Which parts of the system were reused from open source and under what licence.
15. What the evaluation set's bias is, and how the numbers should therefore be read.

## 5. Stage 3 report structure (outline)

1. Abstract
2. Problem & motivation (Stage 1 §1, tightened)
3. Stage 2 → Stage 3 deviations (**[log](01_REQUIREMENTS.md#3-stage-2-versus-stage-1-deviations-log) plus ADR-0001**)
4. System architecture ([04](04_SYSTEM_ARCHITECTURE.md), redrawn)
5. Design decisions and ADRs ([05](05_TECH_STACK_AND_ADRS.md))
6. Implementation — modules, real structure ([08](08_DATA_MODELS_AND_API_CONTRACTS.md))
7. Open-source research and reuse decisions ([02](02_OPEN_SOURCE_RESEARCH.md))
8. Verification design and its stated limits ([04 §5](04_SYSTEM_ARCHITECTURE.md#5-citation-verification-design))
9. UI/UX ([07](07_UI_UX_DESIGN_SPEC.md), real screenshots)
10. Testing ([09](09_TESTING_STRATEGY.md), real output)
11. Evaluation ([10](10_EVALUATION_METRICS.md), real numbers with methods)
12. Limitations and future work
13. Individual contributions (from actual commit authorship, [13](13_TEAM_CONTRIBUTIONS.md))
14. References — Stage 3 cites only what it read. Stage 2's suspected numbering error
    ([I-01](03_GAP_ANALYSIS.md#31-internal-inconsistencies-found-in-the-stage-2-report)) was **checked
    in Phase 7 and did not reproduce**: zero dangling and zero orphaned references in the Stage 2
    text. Worth being able to explain, because it shows an audit finding being closed by measurement
    rather than assumed.

The draft is written: [16_STAGE_3_REPORT_DRAFT.md](16_STAGE_3_REPORT_DRAFT.md), following exactly this
outline. It is **not submission-ready** — see its §15 for what is missing.

## 6. Anti-fabrication checklist before submission

- [ ] Every quantitative claim traces to an artifact in [12](12_STAGE_3_EVIDENCE_TRACKER.md)
- [ ] Test counts are ours, from a real run, with output pasted
- [ ] No commit hash, PR number or contribution percentage that isn't real
- [ ] Every screenshot is capturable and labelled; nothing simulated
- [ ] No third-party benchmark presented as ours
- [ ] Every threshold traced to the calibration run
- [ ] Sample sizes stated everywhere
- [ ] False-`Verified` and false-abstention rates reported, not just the flattering ones
- [ ] Python-version deviation documented (ADR-0001)
- [ ] Chroma status documented truthfully, whichever way it went
- [ ] Stage 2's citation numbering corrected, not inherited
- [ ] All three members can answer §4.4 unaided
- [ ] Proof-reading pass on "verified", "proven", "confirmed", "accuracy", "hallucination"
