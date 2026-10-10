# 05 — Tech Stack & Architecture Decision Records

**Status:** Phase 1 baseline · Last updated 2026-10-08
**Related:** [Architecture](04_SYSTEM_ARCHITECTURE.md) · [Open-Source Research](02_OPEN_SOURCE_RESEARCH.md) · [Charter](00_PROJECT_CHARTER.md)

---

## 1. Stack summary

| Layer | Choice | Licence | Role | Cost |
|---|---|---|---|---|
| Language | Python **3.14.6** (pinned, ADR-0001) | — | Core | Free |
| PDF primary | `pypdf` 6.19.0 | BSD-3-Clause | Page-wise extraction | Free |
| PDF fallback | `pdfplumber` 0.11.10 | MIT | Difficult layouts | Free |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Apache-2.0 | Semantic retrieval | Free, ~90 MB once |
| Vector store | `chromadb` 1.5.9 | Apache-2.0 | Local persistence | Free |
| Lexical fallback | `scikit-learn` 1.9.x | BSD-3-Clause | TF-IDF retrieval + fallback profile | Free |
| Generator (optional) | `google/flan-t5-small` | Apache-2.0 | Abstractive answers | Free, ~308 MB once |
| Generator (default) | Extractive, own code | ours | Deterministic answers | Free |
| Verifier | Own code | ours | Support scoring + labels | Free |
| UI | `streamlit` 1.65.0 | Apache-2.0 | Application | Free |
| Tests | `pytest` 9.1.1 | MIT | Automated validation | Free |
| VCS | Git / GitHub | — | Contribution evidence | Free for students |

**Total paid cost of the baseline design: INR 0.**

---

## ADR-0001 — Pin the Python version

**Status:** **Accepted 2026-10-08** — human decision recorded in Phase 2. Pin: **CPython 3.14.6** (`C:\Python314\python.exe`). Option **A**.

**Context.** Stage 2 §3.2 says "use one fixed version" and §2.3 reports a run on **Python 3.13.5**.
This machine exposes **only Python 3.14.6** (`C:\Python314\python.exe`), and `py -0p` lists no other
interpreter. Most of the stack is already installed for 3.14.

Compatibility evidence gathered 2026-10-08 from the PyPI JSON API:

| Package | `requires_python` | Latest | Wheel tags | 3.14 risk |
|---|---|---|---|---|
| `chromadb` | `>=3.9` | 1.5.9 | **`cp39-abi3`** (+ source) | Low — abi3 wheels are forward-compatible, so the `cp39-abi3-win_amd64` wheel should install on 3.14 |
| `sentence-transformers` | `>=3.10` | 6.1.0 | `py3-none-any` | None (pure Python) |
| `streamlit` | `>=3.10` | 1.65.0 | `py3-none-any` | None |
| `scikit-learn` | `>=3.11` | 1.9.1 | `cp311…cp315` | **None** — a native `cp314` wheel exists |
| `pypdf` | `>=3.9` | 6.19.0 | `py3-none-any` | None |
| `pdfplumber` | `>=3.8` | 0.11.10 | `py3-none-any` | None |

**Options.**

| Option | Pros | Cons |
|---|---|---|
| **A. Develop and pin on 3.14.6** | Available today; `cp314` sklearn wheel exists; most deps pre-installed; chromadb abi3 should work | Deviates from Stage 2's stated 3.13.5; newest interpreter, most likely place for an unforeseen ecosystem break |
| B. Install 3.13.x and pin there | Matches Stage 2 exactly; largest ecosystem compatibility | Costs setup time; contradicts the "3–5 days" budget; `scikit-learn` needs `cp313` (available) |
| C. Develop on 3.14, state 3.14 in Stage 3 | Honest and current | Requires an explicit Stage 3 deviation note |

**Recommendation: Option A, with an explicit logged deviation.** Rationale: the deviation is a
*superset* of the Stage 2 constraint (3.10+), not a violation of it; the environment already has
almost everything installed; and installing a new interpreter is pure overhead against the deadline.
Whichever is chosen, Phase 2 must verify `chromadb` actually imports and persists on it — that is
[R-01](14_RISK_REGISTER.md), and the check is a Phase 2 gate item.

**Consequence if wrong:** a `chromadb` native-extension failure on 3.14. Fallback is to drop to the
in-memory store and log it (see [Architecture §6](04_SYSTEM_ARCHITECTURE.md#6-failure-modes-and-degradation)).

**Decision of record (2026-10-08).** The human team lead chose **Option A: develop and pin on
CPython 3.14.6**, on the grounds that the interpreter is already present, a native `cp314`
`scikit-learn` wheel exists, and installing another interpreter spends budget that the 3–5 day
deadline does not have. This is a **logged deviation from Stage 2's stated 3.13.5** — not a
violation of Stage 2's actual constraint, which was "Python 3.10 or newer". The deviation is carried
as D-10 in [01_REQUIREMENTS.md §3](01_REQUIREMENTS.md#3-stage-2-versus-stage-1-deviations-log) and
must be restated in the Stage 3 report.

The `chromadb` verification promised above was executed in Phase 2 item 3.10; its real result is
recorded in [14_RISK_REGISTER.md](14_RISK_REGISTER.md) risk R-01 and in
[15_PROGRESS_TRACKER.md §8](15_PROGRESS_TRACKER.md#8-measurements-taken). No result was assumed.

---

## ADR-0002 — pypdf primary, pdfplumber fallback

**Status:** Accepted (inherited from Stage 2 §2.1.1)

**Context.** Stage 1 specified `PyPDF2`. Stage 2 corrected this to `pypdf`, the maintained successor.

**Decision.** `pypdf` for all pages; `pdfplumber` re-extracts only pages where `pypdf` returned
almost no text.

**Why.** `pypdf` is pure-Python, fast, dependency-light, and its page iteration is straightforward.
`pdfplumber` is slower and heavier (it renders layout) but is genuinely better at multi-column and
table-heavy text. Retrying only near-empty pages gets the benefit without paying the cost on every
page.

**Rejected:** `PyMuPDF` (much faster, but AGPL-adjacent licensing concerns and a heavier binary —
Stage 2 chose not to introduce it), `pdfminer.six` alone (what `pdfplumber` wraps; no advantage in
using it directly).

---

## ADR-0003 — Sentence splitting without an NLP dependency

**Status:** Accepted (new — resolves Stage 2 gap [I-02](03_GAP_ANALYSIS.md#31-internal-inconsistencies-found-in-the-stage-2-report))

**Context.** Stage 2 says chunking is "sentence-aware" but never names a sentence splitter or a
dependency for one. This is an unresolved implementation gap.

**Decision.** A small, tested, regex-based sentence splitter in `src/chunking.py`, tuned for academic
prose:

- Split on `.!?` followed by whitespace and a capital/quote/digit, plus a hard newline.
- Guard against common academic abbreviations: `e.g.`, `i.e.`, `et al.`, `Fig.`, `Eq.`, `No.`,
  `Ref.`, `pp.`, `vs.`, `approx.`, `Dr.`, `Prof.`, and single initials (`A. Smith`).
- Guard against decimals (`3.14`) and version numbers.
- Collapse whitespace; drop empty fragments.

**Why not NLTK/spaCy?** Both are real options, but each adds a heavyweight dependency (spaCy also
brings a compiled model download) for a job a well-tested regex handles acceptably on academic text.
Stage 2's whole design philosophy is minimising weight so the project runs on a plain laptop. A
regex splitter is ~40 lines, fully testable, and explainable in a viva — which matters here.

**Honest limitation.** A regex splitter mishandles some quotations and bullet-heavy slides. Recorded
as a limitation rather than hidden.

**Rejected:** `nltk` (large download for Punkt), `spacy` (model download + binary), `langchain`
text splitters (violates C7).

---

## ADR-0004 — Chroma for persistence, with a licence caveat to record

**Status:** Accepted

**Context.** Stage 2 specified Chroma. It is not currently installed.

**Decision.** `chromadb` `PersistentClient` as the semantic-profile store, with the deterministic
in-memory store as the fallback and the test store.

**Why.** It persists embeddings + metadata to a local directory with no database server — exactly
matching C3 and the "no server" claim in Stage 2 Table 4. It also supports metadata filtering, which
we may want later.

**Caveat to record in Stage 3:** `chromadb 1.5.9`'s PyPI metadata reports
`license: None` (the `info.license` field is empty) while the project is widely distributed under
Apache-2.0. We consume it as a **pip dependency**, never vendor it, and our report will cite the
project's own repository licence rather than PyPI's incomplete metadata field. Worth verifying
directly against `github.com/chroma-core/chroma` before the report is written.

**Also record:** Chroma's default index is HNSW (approximate), so top-k membership is not guaranteed
bit-stable across runs. See [Architecture §8](04_SYSTEM_ARCHITECTURE.md#8-determinism).

---

## ADR-0005 — Two profiles, one pipeline

**Status:** Accepted (inherited from Stage 2 §1.1)

**Context.** The project must be demonstrable without any model download, but must also use semantic
retrieval when available.

**Decision.** Two backends behind identical protocols, selected by config, never by branching through
the pipeline:

| | Semantic profile | Offline profile |
|---|---|---|
| Embedding | MiniLM (384-dim) | TF-IDF (sparse) |
| Store | Chroma persistent | In-memory |
| Generator | FLAN-T5-small (optional) | Extractive |
| Network | One-time download | None at all |

**Why it matters.** The offline profile is what makes the 17 mandated test scenarios runnable in CI
without downloads, and it is the profile that guarantees our "no API key, no internet" promise
(NFR-01). It is a first-class citizen, not a degraded afterthought.

---

## ADR-0006 — Never describe cosine similarity as proof

**Status:** Accepted (non-negotiable academic-integrity decision)

**Context.** Stage 1 §4.1 called the similarity check "a proxy, not a proof" — correct. Stage 2 §7.2
gives the viva answer: "No. It measures relatedness in an embedding space." Stage 2 replaced the
label "Hallucinated" with "Unsupported" for the same reason.

**Decision.** Three-layer enforcement:

1. **Wording.** `Verified` is defined in
   [Architecture §5.6](04_SYSTEM_ARCHITECTURE.md#56-what-verified-means--exact-wording) with exact
   permitted and forbidden phrasing. The report, the UI and the viva all use it.
2. **Naming.** The word "hallucination" is reserved for evaluation discussion; the system never emits
   it as a label.
3. **Design.** The middle band exists precisely because the extremes are not trustworthy — which is
   the architectural expression of the same doubt.

**Why it matters.** This is the single decision an examiner is most likely to probe, and the one
most likely to expose a team that overclaims. Getting it right is worth more than any feature.

---

## ADR-0007 — Verifier scope: precision-first abstention

**Status:** Accepted

**Context.** `aberaio/sourcecheck` (GitHub API-verified, licence `NOASSERTION`) states its design
principle explicitly: it checks whether a claim is **sourced**, not whether it is **true**, and it
prefers `not_verifiable` over a wrong `supported`. Its ideas informed ours; **no code was used**
(licence forbids it).

**Decision.** When support is ambiguous, the system must not claim support.

- A marker that does not resolve ⇒ `Unsupported` (never silently dropped).
- Low similarity ⇒ `Needs Review` at minimum, never a confident pass.
- No evidence retrieved ⇒ abstain entirely.

**Consequence, accepted knowingly:** we will produce more `Needs Review` labels than a
maximum-agreement system would. That is the correct trade-off for a tool whose purpose is academic
integrity, and it must be explained as a deliberate precision-first choice.

---

## ADR-0008 — No citation re-attribution in the MVP

**Status:** Accepted

**Context.** `GooTec/citation-guard` (MIT, 0 stars) implements a three-step policy: verify → if
unsupported but *another* provided passage supports it, **re-point the citation** → else flag.

**Decision.** We do **not** implement re-attribution.

**Why.** Re-attribution *changes the citation*. In a tool whose entire value proposition is "here is
where this claim came from", silently moving a citation to a different page destroys the very
guarantee we are selling. A user who sees `[S1, p.5]` reasonably believes the claim was checked
against page 5.

We could implement it later as an *explicit user action* ("re-check this claim against the whole
collection and show me better-supported sources"), where the user — not the system — decides. That
is a good P2 feature and a natural viva answer.

---

## ADR-0009 — Build standalone; reuse libraries, not a fork

**Status:** Accepted — the Phase 0 headline decision

**Full evidence:** [02_OPEN_SOURCE_RESEARCH.md §4](02_OPEN_SOURCE_RESEARCH.md#4-weighted-comparison)
(weighted scoring: standalone **9.00**, hybrid **8.00**, fork paper-qa **5.45**, NexusRAG **5.70**,
DocsGPT **3.65**).

**Decision.** **Strategy B** — build a lightweight standalone project using reusable open-source
libraries, plus a disciplined subset of Strategy C (pattern-level attribution with prior-art
citation, no code reuse).

**Why, in one paragraph.** The candidates with real claim-vs-evidence verification
(`urmeo/NexusRAG`, `GooTec/citation-guard`, `aberaio/sourcecheck`) each break a hard constraint —
Ollama + a 3B verifier model, or an unusable licence. The licence-clean, high-quality projects
(`Future-House/paper-qa`, `arc53/DocsGPT`) do not verify claims at all, so adopting them costs days
and still leaves our entire contribution to be written on top of someone else's architecture.
Standalone from Apache-2.0/BSD/MIT libraries is the only route that satisfies Stage 2 inside 3–5 days,
keeps every line explainable at viva, and produces unambiguous individual-contribution evidence.

**Attribution owed** (patterns re-implemented, cited as prior art, no code copied):

| Prior work | Pattern borrowed | URL | Licence |
|---|---|---|---|
| `paper-qa` | Page-granular citations; filter markers against the retrieved set; numerical anchoring | https://github.com/Future-House/paper-qa | Apache-2.0 |
| `NexusRAG` | Verification ordering: validate markers → check support → strip/flag | https://github.com/urmeo/NexusRAG | MIT |
| `citation-guard` | Verify/re-attribute/flag policy (we implement verify/flag only) | https://github.com/GooTec/citation-guard | MIT |
| `sourcecheck` | Precision-first abstention philosophy (ideas only) | https://github.com/aberaio/sourcecheck | `NOASSERTION` — **no code used** |
| `citation-needed-api` | Claim-level audit UX concept | https://gitlab.wikimedia.org/repos/future-audiences/citation-needed-api | MIT |
| `greyskyAI/PDF_RAG_with_Citations` | Local Streamlit + MiniLM + page-metadata plumbing reference | https://huggingface.co/spaces/greyskyAI/PDF_RAG_with_Citations | Space licence unverified |

**Rejected alternatives:**

| Option | Why rejected |
|---|---|
| Fork `paper-qa` | Our contribution becomes an upstream patch → weak individual evidence; days of integration; its answerer is inference-API-based and stubs out without a token |
| Fork `urmeo/NexusRAG` | Violates C1, C2 and C6 (Ollama + 3B model + FastAPI); 4 stars, brand-new, maintainability unproven |
| Fork `arc53/DocsGPT` | A platform, not a tool; meeting our brief means deleting most of it |
| Use `StadynR/scientific-paper-chat-rag` | **GPL-3.0** — copyleft risk on academic work |
| Use `sourcecheck` / `TrustLayer` / `QA_RAG` | **No licence** — legally unusable for reuse |
| `StadynR`, `citation-verifier`, `citation-needed-api` | Wrong problem (remote sources / Wikipedia), dormant, or OpenAI-dependent |

---

## ADR-0010 — Streamlit, and its honest limits

**Status:** Accepted with a documented constraint

**Context.** C6 forbids replacing Streamlit. The brief demands a "premium" UI.

**Decision.** Streamlit, with scoped custom CSS, `st.cache_resource` for model reuse, and honest
state design.

**Known Streamlit limitations** (catalogue in
[07_UI_UX_DESIGN_SPEC.md §7](07_UI_UX_DESIGN_SPEC.md#7-streamlit-implementation-method-and-known-limitations)):

| Limitation | Consequence | Workaround |
|---|---|---|
| CSS injected into an iframe | Global selectors can break Streamlit internals | Namespace all rules under our own root class |
| Rerun-on-interaction model | State must live in `st.session_state`; no fine-grained reactivity | Explicit state dict, cached resources |
| Limited component primitives | No true design-system components | Composed containers + CSS |
| No real client-side routing | No per-tab URLs | `st.radio`/`st.sidebar` navigation |
| Everything rerenders | Careless code causes flicker and lost focus | `@st.cache_resource` for models/stores |

**If a UI requirement genuinely cannot be met in Streamlit**, the procedure is: document the exact
limitation, the alternative, the engineering cost, and request approval. Do not unilaterally migrate
to React/Next.js. To date, no requirement in [FR-41→47](01_REQUIREMENTS.md#27-ui) requires it.

---

## ADR-0011 — Optional FLAN-T5-small, not required

**Status:** Accepted (inherited from Stage 2 §2.1.4)

**Decision.** `google/flan-t5-small` is a **strictly optional** enhancement. The default generator is
extractive.

**Why.** Three reasons, all defensible: (1) ~308 MB download for marginal quality over extractive on
CPU; (2) abstractive generation can *introduce* wording not present in the evidence — which is
precisely the failure mode we exist to detect, so making it the default would be self-defeating;
(3) greedy decoding on CPU is slow, and the demo must be snappy and repeatable.

**Honest framing for the report:** our design deliberately prefers a *verifiable* answer over a
*fluent* one. That is the thesis of the project.

---

## ADR-0012 — Thresholds live in config, never inline

**Status:** Accepted

**Decision.** A single `VerificationConfig` dataclass holds `verified_threshold`,
`review_threshold`, the `0.7`/`0.3` weights, normalisation settings, and the stopword/antonym sets. No
scoring function contains a numeric literal threshold.

**Why.** Stage 2 §2.1.5 is explicit that thresholds are "configuration values, not universal
constants" and "must be calibrated on a manually labelled test set". A threshold buried in a
function is uncalibratable and undefendable in a viva.

---

## ADR-0013 — Treat stage-2 prototype claims as unverified

**Status:** Accepted (integrity decision)

**Decision.** The Stage 2 figures — 10/10 tests, 28 chunks, 11 pages, and the four commit hashes —
are recorded as **historical report claims** in
[03_GAP_ANALYSIS.md](03_GAP_ANALYSIS.md#3-report-claims-vs-workspace-reality) and may not be
presented as current evidence. Stage 2 itself warns its commit IDs "must not be presented as evidence
of an individual's work".

**Why.** Reproducing someone else's unverified numbers into a submitted report is the exact
behaviour this project exists to criticise. We would be doing to our own examiner what LLMs do to
students.
---

## ADR-0014 — Refuse before generating, on query coverage rather than a relevance floor

**Status:** Accepted

**Context.** FR-33 requires explicit abstention when evidence is absent **or insufficient**, and the
architecture originally implemented only the first: an empty index abstains, a non-empty index always
produces an answer. Measured consequence (R-24): on 10 out-of-corpus questions the system emitted 50
claims, **15 of them labelled `Verified`** — about photosynthesis, the 1994 Nobel Prize in
Literature and the formula for table salt. The verifier was behaving correctly; it was verifying an
answer that should never have been built.

The obvious fix is a floor on `relevance_score`. It was implemented as a sweep before anything was
shipped, and it **does not work**: on 48 labelled questions the answerable and unanswerable top-1
cosine ranges overlap (0.138–0.257 against 0.072–0.192), so every floor that catches most
unanswerable questions also kills at least five of eight answerable ones. TF-IDF cosine over shared
academic prose is dominated by vocabulary both classes contain.

**Decision.**

1. A pre-generation gate refuses when the fraction of the question's **content words** present in the
   retrieved passages falls below `AbstentionConfig.min_query_coverage` (default **0.50**, swept on
   labelled data). Coverage separates the classes where cosine does not: answerable minimum 0.667,
   clear unanswerable maximum 0.250.
2. The gate runs **before** the generator, so a refusal produces no claims at all. Verification is
   unchanged and still runs on every claim of every real answer.
3. A question with no content terms after stopword removal is **not** refused. Absence of signal is
   not evidence of absence.
4. The threshold is configuration, in the spirit of ADR-0012, and the published sweep includes the
   operating point that scores better on the labelled set (0.65) and was still rejected for having a
   0.017 margin to the nearest answerable case.
5. The refusal names the query terms that failed to match, and the retrieved passages are still
   returned, so the user can check the refusal instead of trusting it.

**Consequence, accepted knowingly.** The gate is lexical. Six adversarial labelled cases — whose
vocabulary overlaps the corpus while the answer does not exist — are still answered confidently.
They stay in the labelled set so the measured 0.750 cannot be improved by deleting them, and closing
the gap requires entailment rather than a better threshold. This is a **new** precision-first trade
in the same direction as ADR-0007: the system refuses rather than quotes something irrelevant.

---

---

## ADR-0015 — An antonym is only a contradiction if it is about the same thing

**Status:** Accepted

**Context.** The antonym check answers "does the passage use the opposite of the claim's direction
word?". For six phases that was the whole rule, guarded by unit tests. Ten labelled antonym cases
added in Phase 7 ([10 §4c](10_EVALUATION_METRICS.md)) showed it was not enough. `ant_09` — the
claim "The paid API expenditure increased after Stage 2", against a 300-character passage about
reproducibility and blind trust — was reported `contradiction_detected`, because the passage happened
to contain "reduces" in an unrelated clause.

A false contradiction is worse than a missed one. It does not merely fail to catch an error; it tells
the user the source says the opposite, and it does so with the same confident explanation a real
detection carries. The user who checks finds a table row about blind trust, and now has reason to
distrust every other label the system produced.

**Decision.** An opposite direction is a contradiction only when the claim shares vocabulary with
**the sentence carrying it**. One exemption: if the passage is a single sentence, the check proceeds
regardless, because there is nowhere else the claim could be about — without it,
"It was profitable." against "It was expensive." would stop being detected.

**Consequence, accepted knowingly.** The gate is a *decline* rule, so it pushes toward missing a
contradiction rather than inventing one — the same direction ADR-0007 takes for support scores. A
test asserts its result set is a subset of the unguarded one across 100+ word pairs, so it can never
introduce a detection. It is a lexical proxy for "about the same thing", not a parse; a claim and a
passage that are genuinely about the same subject using entirely different vocabulary will still be
missed.


---

## ADR-0016 — A hosted model is an optional profile, not a dependency

**Status:** Accepted

**Context.** The product direction is: upload any document, retrieve, answer with citations, and
check whether those citations hold up. Answer *quality* is bounded by the generator, and the
extractive generator can only quote sentences already present in the retrieved passage. It cannot
paraphrase, cannot synthesise across passages, and cannot answer a question whose answer is assembled
from three different pages. That is a real ceiling, and it is a ceiling on the part of the product
users perceive as "the assistant".

The obvious fix is a stronger model behind the same RAG pipeline. That has been declined twice
already on the grounds that it weakens the guarantees this project rests on. Those objections are
recorded below rather than argued away, because two of them still stand.

**What was accepted, and why it does not break the guarantees.**

1. **The offline default is untouched.** `ExtractiveGenerator` remains the default; a fresh clone
   reproduces every number in the report with no key and no network. The hosted profile is selected
   explicitly, per deployment.
2. **The generator signature is the enforcement.** `generate(question, evidence, max_sentences)`
   hands the hosted model the *same* retrieved passages and nothing else. It cannot see the corpus,
   the file paths, or any other document. "Related to uploaded documents only" is therefore a
   property of the interface, not a promise in a prompt.
3. **The model is never trusted about its own citations.** Brackets in the model—s output are
   *stripped* before claims are built, and every claim is re-attributed to a retrieved chunk by the
   same lexical rule the local generators use. The verifier then re-resolves every marker
   independently. A model that writes `[S7, p.2]` when it was given only `S1` gets no such marker.
4. **Every failure degrades to extractive with a recorded reason.** No key, 401, 429, unreachable
   host, non-JSON body, missing content, unattributable text. The answer carries `degraded=True` and
   the reason, so a degraded run never looks like a full run.
5. **The key never enters a config, a log, a screenshot or a `repr`.** It is read from
   `OPENROUTER_API_KEY` at call time and not retained. `test_repr_never_contains_the_key` and
   `test_a_failure_message_never_contains_the_key` are the enforcement.

**What is genuinely weaker, and is not claimed away.**

* **Determinism.** NFR-03 is scoped to the offline profile. `temperature=0` and `seed=0` are sent
  and make most hosted answers stable, but hosted inference is not *guaranteed* deterministic and the
  report must not say it is.
* **An abstractive generator drifts from its evidence.** This is the failure the project exists to
  detect (R-08), and adopting a hosted model makes it more likely rather than less. The mitigation
  is that the verifier is unchanged and still labels every claim, but the honest position is that
  *verification quality on hosted answers is unmeasured* until someone runs the labelled set through
  this profile. It is listed as `not measured` in [10](10_EVALUATION_METRICS.md) rather than assumed
  to transfer from the extractive profile — the two produce different claim distributions, and an
  extractive claim is a near-substring of its passage while a hosted one is not.

**The free-tier default is a verified fact, not a memory.** `DEFAULT_REMOTE_MODEL` was taken from
the live catalogue at `https://openrouter.ai/api/v1/models`: 458 models, **15** carry `:free` and
price at `{"prompt": "0", "completion": "0"}`. **None are from meta-llama, qwen, deepseek,
mistralai or openai** — all of which are the ids most tutorials still name, so shipping one of
those as a default would ship a broken default. `google/gemma-4-26b-a4b-it:free` is present,
instruction-tuned, with a 262,144-token context. It will go stale; a dead id degrades rather than
crashes, and the model is overridable so fixing it needs no code change.
`test_the_default_model_is_a_free_one` fails the build if a paid id is ever made the default.

**Consequence.** `tests/test_hardening.py::TestSecuritySweep::test_sec08` previously asserted that
`generator.py` imports no HTTP client. That premise is now false by decision, so the test was
restated rather than deleted: `embeddings.py` still may not import one, a new test pins the network
surface to exactly one call site, and another asserts the default config never constructs the hosted
generator. A sweep that merely permitted the import without pinning reachability would be weaker
than the one it replaces.

---

## ADR-0017 — The advisor suggests; it never edits

**Status:** Accepted

**Context.** The verifier produces three labels and a reason code. That answers "what did the system
find" and leaves the user to work out what to do, which is the least useful possible output for
someone trying to fix a document. The product requirement is that a flagged citation comes with a
correction.

The tempting version has the system rewrite the claim automatically. That is refused outright:
silently altering a claim and its citation would destroy the traceability guarantee the entire
project exists to provide, and a user who cannot tell what changed cannot check what changed.

**Decision.** `src/advisor.py` maps each `Reason` to an action code plus a specific sentence, and
builds a pasteable prompt for a general-purpose assistant. It never modifies the answer, never
mutates a document, and never re-verifies.

Two conservative choices are deliberate and tested:

* **`weak_support` produces no action.** Low lexical overlap is the *documented* weakness of a
  containment-based score on paraphrase (D-26), not evidence of an error. Recommending changes for
  correct paraphrases would train users to ignore the advice, and advice that is routinely wrong is
  worse than none.
* **`no_support` recommends removing the claim**, not rewording it. Zero shared vocabulary is not a
  wording problem; rewording will not make a claim about one subject match a passage about another.

**The repair prompt carries an instruction, not just a request.** It tells the assistant to keep
every number, date, unit and proper noun exactly as the source states them, and never to introduce a
figure not present in the passage. The most damaging "improvement" to a citation is a fluent sentence
with an invented number in it — a rewrite that would pass every check in this system while being
wrong. The prompt is built only from the claim and the retrieved passage, never from the document as
a whole, so it cannot smuggle in context the user has not seen.

**Consequence.** `weak_support` and `supported` yield an empty plan rather than a row saying "no
action needed". An answer with nothing wrong and an answer that was never checked are different
facts, and the UI renders them differently: `AnswerResponse.corrections` is empty in both cases, but
`advise([])` returns an empty `summary_prompt` while `advise([supported])` returns a positive one.
The limit is stated rather than hidden: **this cannot tell whether the *source* is right.** It
compares a claim with the passage that claim cites; if the document itself is wrong, a perfectly
supported citation is still wrong and nothing here detects that.
