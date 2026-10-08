# 07 — UI/UX Design Specification

**Status:** Phase 5 implemented · Last updated 2026-10-08 · Automated checks green; 3 manual checks pending
**Related:** [Architecture](04_SYSTEM_ARCHITECTURE.md) · [ADR-0010](05_TECH_STACK_AND_ADRS.md#adr-0010--streamlit-and-its-honest-limits) · [Requirements §2.7](01_REQUIREMENTS.md#27-ui) · [Progress Tracker §7](15_PROGRESS_TRACKER.md#7-test-results)

---

## 1. Design intent

**Nature-inspired academic research workspace.** The feeling of a well-lit library study desk:
warm paper, deep foliage, quiet surfaces, and nothing shouting.

Three anti-goals, stated so future work does not drift into them:

| Anti-goal | What it looks like |
|---|---|
| Not a chatbot clone | No speech-bubble avatars, no "thinking…" dots theatre, no fake typing animation |
| Not a generic AI gradient | No purple→pink hero gradients, no glassmorphism, no neon glow |
| Not a dashboard-for-metrics | Numbers exist to describe *this user's collection*, never to impress |

The UI's job is to make a student feel they are **checking a claim**, not **trusting a system**. So
the primary interaction is: answer → marker → actual page text → score. Everything else is support.

## 2. Design system

### 2.1 Colour

Warm off-white ground, deep forest primary, sage surfaces. All values chosen for long reading
sessions and for contrast compliance.

| Token | Value | Use |
|---|---|---|
| `--bg-canvas` | `#FBFAF6` | Page background — warm ivory, not pure white |
| `--bg-surface` | `#FFFFFF` | Cards, panels |
| `--bg-surface-sunken` | `#F4F3EC` | Insets, code/passage blocks, table stripes |
| `--border-subtle` | `#E4E1D6` | Hairlines, card borders |
| `--border-strong` | `#CFCABC` | Focused/hover borders, inputs |
| `--primary` | `#1F4D3D` | Deep forest green — primary actions, brand |
| `--primary-hover` | `#2A6152` | Hover/active |
| `--primary-muted` | `#E8F0EA` | Sage tint — chips, active nav, badges |
| `--text-primary` | `#1A1D1A` | Body text — near-black, warm |
| `--text-secondary` | `#5A615A` | Labels, metadata |
| `--text-tertiary` | `#8A908A` | Placeholders, disabled |
| `--verified` | `#2F6B4F` | Verified state |
| `--verified-bg` | `#E7F1EA` | Verified chip background |
| `--review` | `#8A6212` | Needs Review — dark amber, AA on white |
| `--review-bg` | `#FBF2DF` | Needs Review chip background |
| `--unsupported` | `#9B2C2C` | Unsupported — deep red, AA on white |
| `--unsupported-bg` | `#FAEAEA` | Unsupported chip background |
| `--info` | `#2F5D8A` | Informational (abstention, tips) |
| `--info-bg` | `#EAF1F8` | Informational surface |
| `--focus-ring` | `#1F4D3D` | Keyboard focus outline |

Contrast intent: `--text-primary` on `--bg-canvas` and every status colour on its `-bg` chip are
targeted at **WCAG AA (≥ 4.5:1)**. Verify with a real checker during Phase 5 and record the measured
ratios — do not assume.

**Never encode status by colour alone.** Every status chip is colour **+** icon **+** text label.
This is a requirement (FR-45), not a nicety: ~8% of men have some colour-vision deficiency, and this
panel carries the project's actual meaning.

### 2.2 Typography

Web-safe stacks only — no webfont downloads (offline-first, NFR-01).

| Role | Stack | Size | Weight | Notes |
|---|---|---|---|---|
| Display / brand | `Georgia, 'Iowan Old Style', serif` | 28–34 px | 400 | Scholarly, not techy |
| Section heading | same serif | 20–22 px | 600 | |
| Body | `'Segoe UI', system-ui, -apple-system, sans-serif` | 15–16 px | 400 | 1.6 line-height |
| Answer text | same serif | 17 px | 400 | Serif for reading prose |
| Evidence passage | `'SFMono-Regular', Consolas, monospace` | 13.5 px | 400 | Passage must read as *quoted material* |
| Label / eyebrow | sans | 11 px | 600 | `letter-spacing: 0.08em`, uppercase |
| Caption / meta | sans | 12.5 px | 400 | `--text-secondary` |
| Score | `ui-monospace, monospace` | 13 px | 600 | Tabular figures so columns align |

Serif for headings and prose, sans for chrome, mono for quoted evidence. The mono passage font is a
functional choice: it visually separates *the document talking* from *our system talking*, which is
the whole thesis.

### 2.3 Spacing & shape

4 px base scale: `4 · 8 · 12 · 16 · 24 · 32 · 48 · 64`.

| Token | Value |
|---|---|
| `--space-1…8` | 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 px |
| `--radius-sm` | 6 px — inputs, chips |
| `--radius-md` | 10 px — cards, panels |
| `--radius-lg` | 16 px — hero surfaces, upload zone |
| `--shadow-sm` | `0 1px 2px rgba(26,29,26,0.05)` |
| `--shadow-md` | `0 2px 8px rgba(26,29,26,0.07)` |
| `--shadow-lg` | `0 8px 24px rgba(26,29,26,0.09)` |
| `--border` | 1 px `--border-subtle` |
| `--content-max` | 1120 px |

Whitespace is generous but structural: 32–48 px between sections, 16–24 px inside cards, 12–16 px
between related fields. Density is the enemy of "premium".

### 2.4 Motion

Restrained, 120–200 ms, `ease-out`. Honour `prefers-reduced-motion`.

| Interaction | Motion |
|---|---|
| Card/button hover | 1–2 px lift + shadow step |
| Expander open | height + opacity, 160 ms |
| Marker hover | background tint, 120 ms |
| State change | 150 ms cross-fade |

**No** looping animation, no skeleton shimmer, no bouncing, no typewriter effects, no confetti on
"Verified". A tool about intellectual honesty should not celebrate.

## 3. Layout

### 3.1 Shell

```text
┌──────────────────────────────────────────────────────────────────────┐
│  ▮ Verdant Scholar      RAG Academic Research Assistant             │  header 64px
│                              local-only · no API keys · v0.1        │
├────────────┬─────────────────────────────────────────────────────────┤
│  SIDEBAR   │  MAIN                                                   │
│  248 px    │  max-width 1120px, centred, 32px gutters               │
│            │                                                         │
│  Dashboard │  ┌───────────────────────────────────────────────────┐  │
│  Library   │  │  page header                                       │  │
│  Workspace │  │  ───────────────────────────────────────────────── │  │
│            │  │  content                                           │  │
│  ──────    │  │                                                    │  │
│  Settings  │  └───────────────────────────────────────────────────┘  │
│            │                                                         │
│  ──────    │                                                         │
│  index     │                                                         │
│  status    │                                                         │
├────────────┴─────────────────────────────────────────────────────────┤
│  footer: backend · model status · profile                            │
└──────────────────────────────────────────────────────────────────────┘
```

Sidebar sections: **navigation** (Dashboard / Library / Workspace), **Index status** (live:
backend name, document count, page count, chunk count, persistence path), **Settings** (chunk size,
overlap, `top_k`, thresholds, generator mode).

Putting live index status permanently in the sidebar is deliberate: at every moment the user can see
*what the system is actually working with*. No invented numbers.

### 3.2 Responsive

| Breakpoint | Behaviour |
|---|---|
| ≥ 1200 px | Full layout, 248 px sidebar, 2-column where useful |
| 768–1199 px | Sidebar collapses to a top nav row; main full-width |
| < 768 px | Single column; evidence inspector stacks below the answer; verification chips wrap |

The verification panel and evidence passage must **never** be the thing that gets hidden on a small
screen. If they are not visible, the user cannot check anything, and the product has failed.

## 4. Surfaces

### 4.1 Dashboard

**Purpose:** orient the user, show the value in one line, and get them to the upload.

```text
╭──────────────────────────────────────────────────────────────────╮
│  ▮ Verdant Scholar                                             │
│                                                                  │
│  Answers from your papers — with citations you can check.       │
│  Every claim is compared against the exact page it cites.        │
│                                                                  │
│  [ 12 documents ]  [ 1,043 pages ]  [ 9,214 chunks ]            │
│                     live from the index                          │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯

╭─ Upload ────────────────────────────────────────────────────────╮
│                                                                  │
│        ⬆   Drop academic PDFs here, or browse                    │
│            PDF only · up to 50 documents                          │
│            Scanned/image-only PDFs are not supported (no OCR)     │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯

  [ Recent questions ]  [ Ask a question → ]   ← quick actions
```

Rules: the three stat tiles read from `pipeline.index_stats()`; the upload zone states limits and the
OCR limitation *before* the user uploads anything; quick actions deep-link to the Workspace.

### 4.2 Document library

| Column | Content | Source |
|---|---|---|
| Status | Indexed / Indexing / Failed | Real index state |
| Filename | Sanitised display name | Real filename |
| Pages | Page count | Measured |
| Chunks | Chunk count | Measured |
| Engine | Semantic / Lexical | Real backend |
| Actions | Reindex · Remove | Calls pipeline APIs |

Failed rows must show the real reason. Remove must confirm, because it deletes index state. Empty
state: an illustration-free, single-line explanation plus the upload action — no mock rows.

### 4.3 Research workspace

```text
╭─ Ask a question ────────────────────────────────────────────────╮
│  [ What technology stack is listed in Table 1?          ] [Ask]  │
╰──────────────────────────────────────────────────────────────────╯

╭─ Answer ────────────────────────────────────────────────────────╮
│  The Stage 2 report selects MiniLM-L6-v2 for embeddings and     │
│  Chroma for local vector storage [S1, p.5]. Chroma is chosen    │
│  because it persists locally without a database server          │
│  [S1, p.9].                                                      │
│                                                                  │
│  [S1, p.5] [S1, p.9]   ← clickable, keyboard-focusable          │
╰──────────────────────────────────────────────────────────────────╯

╭─ Verification ──────────────────────────────────────────────────╮
│  ● Verified     2 claims     support 0.81 · 0.76                │
│  ◐ Needs Review 0 claims                                            │
│  ✕ Unsupported  0 claims                                            │
│                                                                  │
│  ● Claim 1 · support 0.81   [inspect evidence →]                │
│    similarity 0.79 · overlap 0.86 · number check passed          │
╰──────────────────────────────────────────────────────────────────╯
```

The verification summary shows **counts and the worst score** — the honest headline. It must never
show a single averaged "confidence" percentage for the whole answer, because averaging hides the one
bad claim that matters.

### 4.4 Evidence inspector

Opens when a marker is selected. This is the product's centre of gravity.

```text
╭─ [S1, p.5] ─────────────────────────────────────────────────────╮
│  FAI_PE_Microproject_Stage_2_Report_Revised.pdf   page 5 of 15   │
│                                                                  │
│  SUPPORT      ● Verified                                         │
│  score        0.81   (similarity 0.79 · overlap 0.86)            │
│  retrieval    0.74   ← relevance to your question                │
│  chunk        S1 · p.5 · c0007                                   │
│                                                                  │
│  ── Passage as retrieved ───────────────────────────────────────  │
│  │ the semantic profile uses sentence-transformers/               │
│  │ all-MiniLM-L6-v2 to convert each evidence chunk into a         │
│  │ dense embedding. Chroma stores the chunk text, embedding and   │
│  │ metadata on the local machine.                                │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  Why this label: the claim's terms are present in the passage    │
│  and the semantic similarity is above the Verified threshold     │
│  (0.62). This indicates correspondence, not formal entailment.    │
╰──────────────────────────────────────────────────────────────────╯
```

Note the deliberate ordering: **retrieval score and support score are shown as separate, separately
labelled rows.** And the explanation ends by restating what the label does not mean.

### 4.5 Verification panel

| State | Icon | Colour | Chip text | Meaning shown to user |
|---|---|---|---|---|
| Verified | ● | `--verified` | `Verified` | Passed the support check at the configured threshold |
| Needs Review | ◐ | `--review` | `Needs Review` | Weak or ambiguous support — you should read the passage |
| Unsupported | ✕ | `--unsupported` | `Unsupported` | No meaningful support, unresolvable marker, or contradiction |

Each row: icon + chip + count + one-line meaning. Colours are supplementary; the icon and text carry
the meaning alone.

## 5. Activity & error states

Every state is designed. A broken-looking state undermines the whole product.

| State | Presentation | Recovery action |
|---|---|---|
| No documents | Calm panel + upload action | Upload |
| Uploading | Progress indicator with real filename | — |
| Parsing | Stage label + page progress | — |
| Indexing | Stage label + chunk count as it grows | — |
| Model loading (first time) | "Loading local model — first run only (~90 MB)" | — |
| Retrieving | Brief stage indicator | — |
| Generating | Brief stage indicator | — |
| Verifying | Brief stage indicator | — |
| Empty result | "No passage in your documents matches this question." + suggestions | Broaden the question / check the library |
| Abstained | Info panel: evidence was insufficient, so no answer was generated | Ask differently / add documents |
| Missing model | Amber panel: which model is missing, what still works without it | Fall back / install command |
| Unsupported file type | Error naming the file and the reason | Remove it |
| Encrypted PDF | Error: password-protected PDFs are not supported | Remove it |
| Scanned PDF | Error: OCR is out of scope, text-based PDFs work | Remove it |
| Corrupt PDF | Error with the underlying cause | Remove it |
| Too many pages | Warning with the actual limit | Split the PDF |
| Injection warning | Amber notice: document text contains instruction-like content; treated as data | Continue / Inspect |
| Storage unavailable | Warning: semantic store unavailable, running in offline mode | Retry / continue offline |

Rule: **never show an error without saying what to do next.**

## 6. Accessibility

| Concern | Implementation |
|---|---|
| Status without colour | Icon + text label always |
| Contrast | AA target for all text; measure and record actual ratios in Phase 5 |
| Keyboard | Sidebar nav, upload, question input, markers, expanders, all focusable in DOM order |
| Focus visible | `--focus-ring`, 2 px, never removed |
| Screen reader | Descriptive labels on every control; chips carry their text; passages in a labelled region |
| Heading order | One `h1` per surface, no skipped levels |
| Motion | `prefers-reduced-motion` disables transitions |
| Zoom | Usable at 200% browser zoom |
| Tabular data | Monospace with tabular figures so numbers align |
| Language | `lang="en"`; non-Latin text must not break layout |

## 7. Streamlit implementation method and known limitations

| Concern | Method |
|---|---|
| Theme | Single `st.markdown("<style>…", unsafe_allow_html=True)` in one helper, called once |
| CSS safety | All rules namespaced under `.vs-*` classes we own; **no** bare element or `.st*` internal selectors |
| State | `st.session_state["index"]`, `["last_answer"]`, `["selected_marker"]`, `["profile"]` |
| Models | `@st.cache_resource` for encoder / generator / store — never reload per rerun |
| Navigation | `st.sidebar.radio` → content switch |
| Cards | `st.container(border=True)` + scoped CSS |
| Expanders | `st.expander` for evidence; the marker/claim mapping stays in our data, not in Streamlit's |
| Status | `st.status` / `st.spinner` for stage labels |
| Tables | `st.dataframe` for the library; `st.columns` for the verification summary |
| Avoid | `unsafe_allow_html=True` with untrusted content — PDF text must be escaped before it goes into HTML |
| Avoid | Global CSS resets (`*`, `body`, `div`); `iframe { … }` hacks; hiding Streamlit's own chrome beyond the header |

**Escaping rule (SEC-04):** any PDF-derived text rendered through `unsafe_allow_html=True` must be
HTML-escaped first. Prefer `st.write`/`st.text` (which escape for you) over HTML injection.

## 8. No-fabrication rules for the UI

Enforced by FR-47 and NFR-12. The UI must never:

- display a document, question, answer, or verification result that did not come from the pipeline in
  this session;
- show a hardcoded "98% accuracy", "12,000 papers indexed", or similar;
- show a citation or score that was not computed;
- hide a degraded backend behind a healthy-looking badge.

If a number is unavailable, the panel shows its empty state. This is both an integrity requirement and
a good design constraint: it forces the UI to be honest by construction.

## 9. Visual checklist (Phase 5 exit)

Verified automatically by `tests/test_ui.py` unless marked otherwise. Ratios are **measured**, not
assumed — see [Progress Tracker §7b.1](15_PROGRESS_TRACKER.md#731-measured-contrast-ratios-wcag).

- [x] Ivory canvas, forest primary, sage surfaces — every spec colour asserted present in the stylesheet
- [x] Serif headings and prose; mono evidence passages — three distinct stacks, and the passage block is asserted to use mono specifically
- [x] Consistent 4 px spacing scale — all eight `--vs-s*` tokens asserted
- [x] All six surfaces render real data — `TestRenderHelpersRun`, 12 tests
- [x] All activity/error states designed and reachable — every ingest reason code has tested recovery text
- [ ] **Status legible with colour removed entirely** — screenshot in greyscale · **manual**
- [x] Contrast ratios measured and recorded — 13 pairs; 12 at AA, the placeholder hint at 3.3:1 against a 3:1 large-text floor
- [ ] **Full keyboard walkthrough completed** — **manual**
- [ ] **1280 px and 768 px both clean** — **manual**
- [x] No global CSS selectors; Streamlit internals unharmed — every selector audited; `.stApp` is the single documented exception
- [x] Zero fabricated values — AST-level greps for placeholder patterns, literal statistics and accuracy claims
- [x] `prefers-reduced-motion` respected; focus outline never removed; no looping animation

### 9.1 Three places the implementation diverged from this spec, and why

1. **Citation markers are real `st.button`s, not clickable spans.** §4.3's sketch implies
   clickable markers. A `<span onclick="…">` cannot be keyboard-activated, so implementing it that
   way would have made FR-43 and the keyboard requirement an accessibility claim that was false. The
   markers keep the mono chip styling; the mechanism is a real widget.

2. **Lookup tables are `MappingProxyType`, not dicts.** §7's `st.session_state` guidance covers
   state, but not module-level constants. AGENTS.md forbids mutable singletons, and the concrete risk
   is specific: a shared mutable table means a later edit could change what a label says without any
   test failing.

3. **The sidebar exposes settings that reconfigure the live pipeline.** `PipelineConfig` was
   designed as construction-time configuration. Making it immutable forever would have meant
   restarting the app to change a threshold, so `reconfigure()` was added — with the guard that a
   change of embedding backend **discards the index**, because TF-IDF and MiniLM vectors are not
   comparable and silently mixing them would produce scores that mean nothing (R-21).