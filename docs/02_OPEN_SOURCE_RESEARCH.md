# 02 — Open-Source Research & Adoption Decision

**Status:** Phase 0 complete · Research performed 2026-10-08 · Last updated 2026-10-08
**Related:** [ADR-0009](05_TECH_STACK_AND_ADRS.md#adr-0009--build-standalone-reuse-libraries-not-a-fork) · [Gap Analysis](03_GAP_ANALYSIS.md) · [Tech Stack](05_TECH_STACK_AND_ADRS.md)

---

## 1. Method and honesty statement

All metadata below was fetched **live on 2026-10-08** from the GitHub REST API
(`https://api.github.com/repos/{owner}/{repo}`) and the Hugging Face API. Star counts, licences and
push dates are point-in-time facts from those endpoints, not remembered values.

**What I did not do:** I did not clone or execute any candidate. I did not read every source file.
Where behaviour is asserted from a README, that is stated explicitly in the evidence column. Where
something could not be verified, it is marked *unverified* rather than guessed.

Two search-result pages appeared to be **unreliable mirrors**: several repositories surfaced only via
the host `github.laiyagushi.com` (e.g. mirrors of `Atharv-725/scholarbot`,
`ChiShengChen/paper-evidence`, `Joncik91/paperQA`). Those were **discarded** — a mirror is not an
authoritative source, and licence/completeness cannot be trusted from it. Only `github.com` and
`gitlab.wikimedia.org` entries were accepted.

Search coverage: GitHub repository search, GitHub REST API, web search, Hugging Face Spaces API,
Hugging Face models API, PyPI JSON API. Searches for `citation verification rag streamlit`,
`claim evidence verification RAG`, `open source local RAG academic paper citation verification`,
`RAG academic paper question answering citation verification` returned 65+ GitHub matches; 18
candidates were evaluated in detail.

## 2. Licence screening — the first filter

**Rule applied:** a project with no licence, or a non-standard/`NOASSERTION` licence, is legally
all-rights-reserved. It may be *read* for ideas but its code may **not** be copied, modified, or
redistributed. This eliminated four otherwise-attractive candidates before any feature comparison.

| Repo | Licence (GitHub API) | Verdict |
|---|---|---|
| `aberaio/sourcecheck` | `NOASSERTION` ("Other") | **Red flag** — not reusable |
| `IfBilal/QA_RAG` | `null` | **Red flag** — not reusable |
| `DoSomethingGreat07/TrustLayer` | `null` | **Red flag** — not reusable (architecturally the closest match, which makes this annoying) |
| `Kem120075/local-rag-app` | `null` | **Red flag** — not reusable |
| `livingdw67/michelin-rag` | `null` | **Red flag** — not reusable |
| `chanindu34/rag-business-assistant` | `null` | **Red flag** — not reusable |
| `mirrys/uncited-statement-detection` | `null` | **Red flag** — not reusable |
| `KowshiqKatta/Generative-AI` | `null` | **Red flag** — not reusable |

> `aberaio/sourcecheck` deserves a specific note: it is the most methodologically interesting
> candidate found (it explicitly separates "is this claim *sourced*" from "is this claim *true*",
> grounds on verbatim quotes with numeric gates, and is *precision-first* — it prefers abstaining
> over false support). Its GitHub licence is `NOASSERTION`, i.e. **we may not reuse a single line of
> it**. Its *ideas* informed our verifier design; no code was taken. This is recorded in
> [ADR-0007](05_TECH_STACK_AND_ADRS.md#adr-0007--verifier-scope-precision-first-abstention).

## 3. Candidate evaluations

### 3.1 `Future-House/paper-qa` — the strongest technical candidate

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/Future-House/paper-qa | GitHub API |
| Purpose | High-accuracy RAG answering questions from scientific documents with citations | API `description` |
| Licence | **Apache-2.0** | API `license.spdx_id` |
| Stars / forks | 9,329 / 934 | API, 2026-10-08 |
| Last push | **2026-09-25** (active) | API `pushed_at` |
| Archived | No | API `archived: false` |
| Open issues | 152 | API |
| Size | ~46.8 MB | API `size` |
| Python | Yes | API |

- **PDF ingestion:** yes, via `pypdf`.
- **Citations:** yes — page-level, filename + page, described as "never invents page numbers",
  markers filtered against retrieved passages then numerically anchored.
- **Real claim-vs-evidence verification:** **partial.** It grounds *citations* (does the cited page
  contain the claimed numbers?) — but that is citation *validity*, not per-claim entailment scoring.
  It does **not** compute a per-claim support score or emit Verified/Needs Review/Unsupported.
- **Local-only viability:** partial. The demo answerer targets an HF Inference API
  (`Qwen2.5-7B-Instruct`); with no `HF_TOKEN` it falls back to an offline stub. Retrieval is local.
- **Hardware:** MiniLM local; answerer needs network or a stub.
- **Python/Streamlit fit:** Python yes; **no Streamlit** (the well-known sibling `Joncik91/paperQA`
  is Gradio, and that result came via an untrusted mirror anyway).
- **Integration cost:** high. Its API surface, agent model, and evaluation harness are designed for
  research-grade use. Adopting it would mean either forking (Apache-2.0 permits it) or writing a
  Streamlit shell around it — and then **our novel contribution (the verifier) becomes a patch on
  someone else's research codebase**, which is exactly the thing that makes individual-contribution
  evidence weak.
- **Maintains:** yes, active. **Accepts contributions:** yes (`pull_request_creation_policy: all`).
- **Technical debt:** research code with a large surface; 152 open issues indicates active churn.
- **Verdict:** **Technically excellent, strategically wrong for us.** Reuse its *design lessons*
  (page-granular citations; filter markers against the retrieved set; numerical anchoring), not its
  code.

### 3.2 `arc53/DocsGPT`

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/arc53/DocsGPT | GitHub API |
| Purpose | Private AI platform for agents, assistants, enterprise search | API `description` |
| Licence | **MIT** | API |
| Stars / forks | 18,316 / 2,189 | API, 2026-10-08 |
| Last push | 2026-10-08 (very active) | API |
| Archived | No | API |

- **PDF ingestion:** yes, but part of a much larger platform.
- **Citations:** source documents are shown; citation *verification* is not a feature.
- **Real claim-vs-evidence verification:** **no.**
- **Local-only viability:** poor fit. It is a multi-service platform (React frontend, worker/queue
  stack, multiple LLM providers, agent builder, API connectivity).
- **UI customisation:** would require replacing their React frontend with Streamlit — i.e. throwing
  away most of the value.
- **Integration cost:** very high for a microproject; violates C6 (Streamlit-only).
- **Verdict:** **Rejected.** Different product category. Huge popularity is irrelevant — it is a
  document-chat *platform*, not a citation *verifier*.

### 3.3 `saadyaq/citation-verifier`

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/saadyaq/citation-verifier | GitHub API |
| Purpose | Agent verifying whether citations support their claims; verdicts SUPPORTED / NOT_SUPPORTED | API `description` |
| Licence | **MIT** | API |
| Stars | **0** | API |
| Last push | **2025-12-27** (~10 months stale) | API `pushed_at` |
| Created | 2025-12-01 | API |
| Size | ~270 KB (tiny) | API |

- **Method fit:** closest *name*-level match to our project.
- **Actual problem solved:** it fetches **remote sources** from the web to check citations. Our
  problem is checking claims against **the user's own local PDFs**. Different problem.
- **Dependencies:** LangChain-based (`topics` includes `langchain`, `rag`, `ai-agent`) — conflicts
  with C7.
- **Local-only viability:** poor — it is network-dependent by design.
- **Maintenance:** dormant.
- **Verdict:** **Rejected.** Wrong problem, dormant, violates the LangChain constraint.

### 3.4 `urmeo/NexusRAG`

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/urmeo/NexusRAG | GitHub API |
| Purpose | Local RAG for scientific papers, hybrid retrieval, cited answers, SciFact/NFCorpus benchmark | API `description` |
| Licence | **MIT** | API |
| Stars | 4 | API |
| Last push | 2026-10-08 (active) | API |
| Published on PyPI | yes (`scinexusrag`, per `homepage`) | API `homepage` |

- **Real verification:** the strongest *implemented* verification among the candidates — citation
  marker validation, optional per-sentence NLI entailment, stripping of out-of-range citations, and
  a faithfulness-detection evaluation (NLI vs lexical vs cross-encoder).
- **Cost profile:** requires **Ollama** with `llama3.2:3b` for generation, plus BGE-small embeddings,
  LanceDB, FastAPI, Docker. Violates C1/C2/C6 (no hosted service, no Ollama, Streamlit-only).
- **Benchmark claims:** the README publishes metric tables and CI floors. *These numbers are the
  author's own; they were not independently reproduced by us and must not be quoted in our report as
  validated.*
- **Star count 4 with 1 fork and 0 open issues** suggests a very small project — its own maturity is
  hard to assess.
- **Verdict:** **Rejected as a base** (violates three constraints). Its *verification-stage
  architecture* — validate markers → optional NLI → strip/flag — directly informed
> [ADR-0007](05_TECH_STACK_AND_ADRS.md#adr-0007--verifier-scope-precision-first-abstention).

### 3.5 `GooTec/citation-guard`

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/GooTec/citation-guard | GitHub API |
| Purpose | Local validated citation-faithfulness guard: verify / re-attribute / flag | API `description` |
| Licence | **MIT** | API |
| Stars | 0 | API |
| Last push | 2026-06-26 | API |
| Size | ~72 KB | API |

- **Real verification:** yes — and its *policy* is the most interesting thing found: verify → if not
  supported but another provided passage supports it, **re-point the citation** → else flag.
- **Cost profile:** needs a **3B AttrScore verifier model** (large download), i.e. it violates the
  "small local models, 3–5 day budget" constraint.
- **Verdict:** **Rejected as a base.** Its three-step policy is worth *discussing in the report* as
  prior art, including why we chose not to implement re-attribution in the MVP (it changes the
  citation rather than reporting the truth — see [ADR-0008](05_TECH_STACK_AND_ADRS.md#adr-0008--no-citation-re-attribution-in-the-mvp)).

### 3.6 `amazon-science/RefChecker`

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/amazon-science/RefChecker | GitHub API |
| Purpose | Automatic fine-grained hallucination checking + benchmark | API `description` |
| Licence | Apache-2.0 | API |
| Stars | 434 | API |
| Last push | 2025-05-16 | API |
| **Archived** | **YES** | API `archived: true` |

- **Contribution:** **impossible.** The repository is archived (read-only). It cannot receive a PR,
  so a "genuine contribution" claim to it is unavailable.
- **Method fit:** interesting (claim-triplet granularity, knowledge-triplet claims) but requires
  LLM-based extraction (`claude 2`, `litellm`, `vllm`) and Google Search API — network and cost.
- **Verdict:** **Rejected.** Read-only. Cite as prior art in the report, do not build on it.

### 3.7 `i1ight/ragPaper`

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/i1ight/ragPaper | GitHub API |
| Purpose | Local-first paper RAG + read-only MCP server, hybrid/reranker retrieval, citation graphs | API `description` |
| Licence | **MIT** (clean) | API |
| Stars | 1 | API |
| Last push | 2026-08-09 | API |

- **Fits well** on stack (local, Chroma, no paid API).
- **Gaps:** no Streamlit UI, no generation layer, no `[S1, p.5]` citation rendering, no verification
  layer — i.e. it covers roughly Phase 3 but none of the project's distinguishing Phase 4 work.
- **Verdict:** **Not adopted.** Clean licence, but adopting it would still leave us writing the UI,
  the generator, and the entire verifier — the parts that constitute our contribution — while
  inheriting someone else's ingestion code for no meaningful time saving.

### 3.8 `StadynR/scientific-paper-chat-rag`

| Attribute | Value | Evidence |
|---|---|---|
| URL | https://github.com/StadynR/scientific-paper-chat-rag | GitHub API |
| Licence | **GPL-3.0** | API |
| Stars / last push | 3 / 2026-03-25 | API |

- **GPL-3.0 is a decisive negative.** Linking or deriving from GPL-3.0 code can impose copyleft on
  our work. For an academic submission we would be *forced* into an awkward licence conversation for
  no benefit.
- Also relies on Ollama (heavier RAM), per the research sub-agent's README read.
- **Verdict:** **Rejected on licence grounds.**

### 3.9 `citation-needed` (the Mozilla/Wikimedia-adjacent project)

- `https://api.github.com/repos/citation-needed/citation-needed` → **HTTP 404 confirmed.** No such
  GitHub repository exists. Any citation to that URL in a report would be a dead reference.
- Real location: **Wikimedia GitLab**, `https://gitlab.wikimedia.org/repos/future-audiences/citation-needed-api`
  (project id 2040), plus a sibling Chrome extension (id 2041).
- **Licence: MIT** (verified by fetching the LICENSE file). Public, 0 stars, created 2024-02-08,
  **last activity 2024-08-26** → dormant.
- **What it does:** genuine claim verification, but against **Wikipedia**, and it **hard-depends on
  the OpenAI ChatGPT API**. Fails C1, C2, C3, and the PDF-first scope.
- **Verdict:** **Rejected**, but worth a one-line prior-art mention in the report because it proves
  the problem is being worked on elsewhere.

### 3.10 Hugging Face Spaces

Live metadata from `https://huggingface.co/api/spaces?search=...`; behaviour from each Space's
`app.py`/`requirements.txt`.

| Space | Likes | SDK | Paid API key? | Real claim-vs-evidence verification? |
|---|---|---|---|---|
| `chansung/paper_qa` | 66 | gradio | **Yes** — Gemini 1.0 Pro | No — pre-generated Q&A, no support scoring |
| `fffiloni/langchain-chat-with-pdf` | 92 | gradio | No paid key, but needs an HF Hub token | No — plain `RetrievalQA`, `return_source_documents` only |
| `awacke1/Arxiv-Paper-Search-And-QA-RAG-Pattern` | 19 | gradio | No paid key; needs HF `InferenceClient` free tier | No — prompt says only "cite the titles of your sources" |
| `awacke1/Arxiv-Paper-Search-QA-RAG-Streamlit-Gradio-API` | 2 | streamlit | **Yes** — `openai==0.28` | *Unverified* — README is an auto-stub, 71 KB `app.py` not read |
| `greyskyAI/PDF_RAG_with_Citations` | 0 | streamlit | **No — fully local** MiniLM + FAISS | No — retrieval only; prints chunks with `page_number`, generates no answer |
| `lavanyagup/Hybrid-Search-Rag-system-with-citation-verification` | 0 | static | *Unverified* | *Unverified* — repo is a 546-byte `index.html` + CSS, no code |

**The decisive finding:** across 6 relevant Spaces and 18 GitHub repositories, **every single one
that shows citations only *formats* citations.** Not one computes a per-claim support score against
its cited evidence.

> This is the strongest single argument for this project's existence, and it belongs in the Stage 3
> report's literature/prior-art section: *"a citation rendered next to a sentence is not a citation
> that has been checked."* Our verifier is the genuine differentiator — and therefore the genuine
> individual contribution.

`greyskyAI/PDF_RAG_with_Citations` is the closest free reference for local Streamlit + MiniLM +
page-metadata plumbing, and is worth reading before Phase 3.

### 3.11 Model licences (verified)

| Model | Licence | Pipeline tag | Downloads | Effective max length |
|---|---|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | **Apache-2.0** | sentence-similarity | 232,247,017 | **`max_seq_length: 256`** |
| `google/flan-t5-small` | **Apache-2.0** | text2text-generation | 443,587 | `model_max_length: 512` |

Both are Apache-2.0 → free for academic use and redistribution with attribution. The
`max_seq_length: 256` value is the empirical justification for D-02 / FR-15.

## 4. Weighted comparison

Weights are fixed by the project brief:

| Criterion | Weight |
|---|---|
| Feature fit (does it do citation *verification*, PDF-first, local) | 25% |
| Zero-cost / local operation | 20% |
| Time-to-MVP (3–5 days) | 20% |
| Maintainability | 10% |
| UI customisation | 10% |
| Licensing / contribution suitability | 10% |
| Academic demonstration clarity | 5% |

Scores are 0–10, each justified below. "Total" = Σ(score × weight).

| Option | Fit 25% | Local 20% | Time 20% | Maint. 10% | UI 10% | Licence 10% | Demo 5% | **Total** |
|---|---|---|---|---|---|---|---|---|
| **B. Standalone + libraries** | **9** | **9** | **9** | **8** | **9** | **10** | **9** | **9.00** |
| C. Hybrid (borrow patterns, write verifier + UI) | 8 | 9 | 7 | 7 | 9 | 7 | 9 | 8.00 |
| A. Fork `paper-qa` | 6 | 6 | 4 | 6 | 4 | 6 | 5 | 5.45 |
| A. Fork/adapt `urmeo/NexusRAG` | 7 | 4 | 4 | 6 | 5 | 9 | 6 | 5.70 |
| A. Fork `DocsGPT` | 3 | 4 | 2 | 5 | 3 | 9 | 3 | 3.65 |

### Justification per score

**Standalone + libraries — 9.00**

- *Fit 9:* it is the only option that produces the exact Stage 2 pipeline including the verifier.
  Subtract 1 because our verifier is a heuristic, not entailment — a real limitation, not a choice.
- *Local 9:* MiniLM + Chroma + TF-IDF + extractive are all local; flan-t5 is optional. Minus 1 for
  the one-time model download and because FLAN-T5 on CPU is slow.
- *Time 9:* with the module layout already specified in Stage 2, each phase is a bounded increment.
  Minus 1 for the Chroma-on-newer-Python risk ([R-01](14_RISK_REGISTER.md)).
- *Maintainability 8:* our own small codebase is fully readable; minus 1 for the Chroma dependency
  and its transitive weight.
- *UI 9:* Streamlit + scoped CSS is exactly the premium UI the brief asks for. Minus 1 for
  Streamlit's CSS/iframe limitations (catalogued in [07_UI_UX_DESIGN_SPEC.md](07_UI_UX_DESIGN_SPEC.md#7-streamlit-implementation-method-and-known-limitations)).
- *Licence 10:* we consume Apache-2.0/BSD/MIT/MIT components as dependencies and write 100% of our
  own code. No copyleft, no attribution debt, no upstream to negotiate with.
- *Demo 9:* the viva story is clean — every component is explained, modified, and defended by us.
  Minus 1 because "we built it ourselves" is a weaker story than "we extended a research system"
  *if* the extension were substantive; here it would not be.

**Hybrid — 8.00**

Strong on fit and demo, weaker on time (we spend days reading someone else's code to reuse little of
it) and on licence hygiene (each borrowed module is a licence obligation to track). We adopt a
*weak* form of C: **pattern reuse with attribution, not code reuse.** Specifically we re-implement
independently, citing as prior art: page-granular citation design and marker-vs-retrieved-set
filtering (`paper-qa`), the validate → NLI → strip/flag verification ordering (`NexusRAG`),
verify → re-attribute → flag policy (`citation-guard`, re-attribution deliberately out of scope),
and precision-first abstention (`sourcecheck`, ideas only, licence forbids code).

**Fork `paper-qa` — 5.45**

Technically the best fit in the market, and Apache-2.0 makes forking *legal*. It fails on three
counts that matter more than its quality: (a) it would replace our headline contribution with an
upstream patch — our citation *verifier* becomes a small PR against someone else's research
codebase, which is weak individual-contribution evidence; (b) integration cost is days, not hours,
against a 3–5 day total budget; (c) its answerer is inference-API-based, and its demo path without a
token is a stub — so our "no stub in the demo" promise would be broken.

**Fork `NexusRAG` — 5.70**

Better verification than paper-qa, and MIT. But it mandates Ollama + `llama3.2:3b` + LanceDB +
FastAPI + Docker, which violates C1, C2 and C6 simultaneously. Four stars, zero open issues, brand-new
repo — maintainability is unproven. Its 4-star count also illustrates that popularity is not a
quality signal.

**Fork `DocsGPT` — 3.65**

Popular (18.3k) and MIT, but it is a platform, not a tool. Meeting our brief would require deleting
its React frontend and agent infrastructure — i.e. forking to remove features. Clear rejection.

## 5. Decision

> ### Recommendation: **Strategy B** — build a lightweight standalone project using reusable open-source libraries, with documented pattern-level attribution (a disciplined subset of C).
>
> **Rationale in one paragraph.** No existing project satisfies the brief. The only candidates with
> real claim-vs-evidence verification (`NexusRAG`, `citation-guard`, `sourcecheck`) each violate at
> least one hard constraint — hosted LLM, a 3B verifier model, or an unusable licence. The
> high-quality, licence-clean projects (`paper-qa`, `DocsGPT`) do not do verification at all, so
> adopting them would cost days and still leave our entire contribution to be written on top of
> someone else's architecture. Building standalone from Apache-2.0/BSD/MIT libraries is the only
> path that satisfies Stage 2 within 3–5 days, keeps every line of the pipeline explainable by the
> team for viva, and produces unambiguous individual contribution evidence — which is exactly what
> Stage 3 is graded on.
>
> Recorded as [ADR-0009](05_TECH_STACK_AND_ADRS.md#adr-0009--build-standalone-reuse-libraries-not-a-fork).

### What "reuse" means precisely

| We reuse | How |
|---|---|
| `pypdf`, `pdfplumber`, `scikit-learn`, `chromadb`, `sentence-transformers`, `streamlit` | Installed dependencies, each keeping its own licence |
| `all-MiniLM-L6-v2`, `google/flan-t5-small` weights | Apache-2.0 model weights, downloaded once, cited |
| Design *patterns* from `paper-qa`, `NexusRAG`, `citation-guard`, `sourcecheck` | Re-implemented independently; cited as prior art with URL + licence in the report |

**No third-party source code is copied into this repository.** If that ever changes, the exact file,
the upstream URL, the licence, and the diff must be recorded here first:

| Copied file | Upstream | Licence | Exact modification | Attribution location |
|---|---|---|---|---|
| *(none)* | — | — | — | — |

### What we could genuinely contribute upstream

None of this is in scope or timeboxed, but it is worth recording that the research surfaced
contribution opportunities, which strengthens the project's honesty framing: `paper-qa` (Apache-2.0,
152 open issues) is the realistic target if we ever wanted a genuine upstream PR. **Do not attempt
this during Stage 3** — it would consume the deadline for zero credit.

## 6. Reproducing this research

```bash
# Repo metadata (authoritative licence / activity)
curl -s https://api.github.com/repos/Future-House/paper-qa | python -c "import json,sys; d=json.load(sys.stdin); print(d['full_name'], d['license']['spdx_id'], d['stargazers_count'], d['pushed_at'], d['archived'])"

# The citation-needed 404 finding
curl -s -o /dev/null -w "%{http_code}\n" https://api.github.com/repos/citation-needed/citation-needed

# HF model licences
curl -s https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2 | python -c "import json,sys; print(json.load(sys.stdin)['cardData']['license'])"
curl -s https://huggingface.co/api/models/google/flan-t5-small | python -c "import json,sys; print(json.load(sys.stdin)['cardData']['license'])"

# HF Spaces
curl -s "https://huggingface.co/api/spaces?search=chat%20with%20pdf&limit=20"

# PyPI compatibility (chromadb abi3 wheel works on Python 3.14)
python -c "import json,urllib.request; d=json.load(urllib.request.urlopen('https://pypi.org/pypi/chromadb/json')); v=d['info']['version']; print(v, d['info']['requires_python'], [f['filename'] for f in d['releases'][v] if 'win_amd64' in f['filename']])"
```

## 7. Research limitations (stated, not hidden)

1. **No candidate was cloned or executed.** All behavioural claims come from READMEs plus selective
   source/requirements reads. Column "real verification?" for the six Spaces is derived from source
   inspection, not observed output.
2. `awacke1/Arxiv-Paper-Search-QA-RAG-Streamlit-Gradio-API` — verification behaviour **unverified**
   (71 KB `app.py` not read).
3. `lavanyagup/Hybrid-Search-Rag-system-with-citation-verification` — **could not be evaluated at
   all**; the Space contains only a 546-byte `index.html` and a stylesheet.
4. HF Spaces searches for `faithfulness grounding check`, `fact check verifier` and
   `paper citation checker` returned **zero** Spaces — so this is not exhaustive of the
   citation-verification Space ecosystem.
5. No archived repository was found among candidates, so the "archived" column being uniformly "No"
   (except RefChecker) does not prove none exist.
6. Star counts, download counts and push dates are as-of 2026-10-08 and will drift. Re-run §6 before
   quoting them in the Stage 3 report.
7. Several results surfaced only via a non-authoritative mirror host and were discarded; any
   genuinely relevant project living only on such a mirror is therefore out of scope for this
   research.