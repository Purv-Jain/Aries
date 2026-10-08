"""Verdant Scholar — Streamlit UI.

This module is a **renderer**. It contains no retrieval, no scoring, no threshold arithmetic and no
citation resolution. Every number it shows came out of `pipeline` in this session; every label came
from a `ClaimVerification`. That is FR-47, and it is enforced two ways: by construction (the imports
below) and by test CT-20, which fails if a leaf module is ever imported here directly.

from types import MappingProxyType
from collections.abc import Mapping, Sequence

1. **No fabricated values.** No "12,000 papers indexed", no invented accuracy figure, no placeholder
   document. A panel with no real data shows its empty state. NFR-12 and §8 of the design spec.
2. **PDF text is escaped before it reaches HTML.** SEC-04. `escape()` is applied to every
   document-derived string, and the upload filename is sanitised again at render time even though
   ingestion already did it — defence in depth, not redundancy.
3. **The two scores never share a visual treatment.** Retrieval relevance and claim support appear
   as separate, separately-labelled rows with different names. FR-26, FR-40.

CSS is namespaced under `.vs-*` and contains no bare element or `.st*` selector, so nothing here can
reach Streamlit's own internals. Design decisions trace to docs/07_UI_UX_DESIGN_SPEC.md.
"""

from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import streamlit as st

from src.models import (
    VERIFICATION_LABELS,
    AnswerResponse,
    ChunkConfig,
    ClaimVerification,
    IngestFailure,
    PipelineConfig,
    ResourceLimits,
    VerificationConfig,
)
from src.pipeline import ResearchPipeline

APP_VERSION = "0.5.0"
BRAND = "Verdant Scholar"
TAGLINE = "Answers from your papers — with citations you can check."

PERSIST_DIR = Path(__file__).resolve().parent / ".chroma"

# Reason code → what the user should do about it. Every error state names a next action,
# because an error with no next action is just a dead end (design spec §5).
#
# All four tables are `MappingProxyType`, not bare dicts. AGENTS.md forbids module-level mutable
# singletons, and the reason is specific rather than stylistic: a shared mutable table can be edited
# by any caller, so a later refactor could quietly change what a label says and no test would fail.
RECOVERY: Mapping[str, str] = MappingProxyType({
    "unsupported_extension": "Remove the file and upload a PDF instead.",
    "empty_file": "The file is zero bytes. Re-export it and try again.",
    "encrypted_pdf": "Remove the password in a PDF reader, then upload the file again.",
    "corrupt_pdf": "The file could not be parsed. Try re-exporting it, or a different copy.",
    "scanned_pdf": "OCR would be needed, and OCR is out of scope. Use a text-based PDF.",
    "too_many_pages": "Split the document into smaller PDFs and upload them separately.",
    "too_large": "Compress the file or upload fewer documents at once.",
    "file_not_found": "The file is no longer where it was. Upload it again.",
    "zero_chunks": "The PDF contained no text long enough to index. Check that it has a text layer.",
    "empty_index": "Upload at least one text-based PDF before asking a question.",
})

LABEL_ICON: Mapping[str, str] = MappingProxyType({
    "Verified": "●",
    "Needs Review": "◐",
    "Unsupported": "✕",
})

LABEL_MEANING: Mapping[str, str] = MappingProxyType({
    "Verified": "Passed the support check at the configured threshold.",
    "Needs Review": "Weak or ambiguous support — read the passage before relying on it.",
    "Unsupported": "No meaningful support, an unresolvable marker, or a detected contradiction.",
})

REASON_TEXT: Mapping[str, str] = MappingProxyType({
    "supported": "The cited passage contains the claim's terms and cleared the threshold.",
    "weak_support": "Some shared vocabulary, below the Verified threshold.",
    "no_support": "The cited passage does not support this claim by the project's heuristic.",
    "unresolvable_reference": "The cited source was never retrieved.",
    "page_mismatch": "The source was retrieved, but not at the page cited.",
    "malformed_marker": "The citation text could not be parsed.",
    "no_marker": "The claim carried no citation.",
    "numeric_mismatch": "A number in the claim is absent from the cited passage.",
    "contradiction_detected": "The claim and the passage differ in polarity.",
})


def escape(value: object) -> str:
    """HTML-escape anything before it goes into markup. SEC-04, and the reason this helper exists.

    Uploaded PDFs are untrusted input. A file containing ``<script>`` must render as visible text, not
    execute. `st.write` and `st.text` escape for us and are preferred everywhere; this is for the
    places where we deliberately emit HTML for layout.
    """
    return html.escape(str(value), quote=True)


# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------

STYLESHEET = """
<style>
:root {
  --vs-bg-canvas:#FBFAF6; --vs-bg-surface:#FFFFFF; --vs-bg-sunken:#F4F3EC;
  --vs-border-subtle:#E4E1D6; --vs-border-strong:#CFCABC;
  --vs-primary:#1F4D3D; --vs-primary-hover:#2A6152; --vs-primary-muted:#E8F0EA;
  --vs-text-primary:#1A1D1A; --vs-text-secondary:#5A615A; --vs-text-tertiary:#8A908A;
  --vs-verified:#2F6B4F; --vs-verified-bg:#E7F1EA;
  --vs-review:#8A6212; --vs-review-bg:#FBF2DF;
  --vs-unsupported:#9B2C2C; --vs-unsupported-bg:#FAEAEA;
  --vs-info:#2F5D8A; --vs-info-bg:#EAF1F8;
  --vs-focus:#1F4D3D;
  --vs-serif:Georgia,'Iowan Old Style',serif;
  --vs-sans:'Segoe UI',system-ui,-apple-system,sans-serif;
  --vs-mono:'SFMono-Regular',Consolas,monospace;
  --vs-r-sm:6px; --vs-r-md:10px; --vs-r-lg:16px;
  --vs-s1:4px; --vs-s2:8px; --vs-s3:12px; --vs-s4:16px; --vs-s5:24px;
  --vs-s6:32px; --vs-s7:48px; --vs-s8:64px;
}
.stApp { background: var(--vs-bg-canvas); }
.vs-header {
  background: var(--vs-bg-surface); border-bottom:1px solid var(--vs-border-subtle);
  padding: var(--vs-s4) var(--vs-s6); margin-bottom: var(--vs-s6);
}
.vs-brand { font-family:var(--vs-serif); font-size:30px; color:var(--vs-primary);
  line-height:1.15; letter-spacing:-0.01em; }
.vs-mark { color:var(--vs-primary); margin-right:10px; }
.vs-tagline { font-family:var(--vs-serif); font-size:16px; color:var(--vs-text-secondary);
  margin-top:var(--vs-s2); }
.vs-badge {
  display:inline-block; font-family:var(--vs-sans); font-size:11px; font-weight:600;
  letter-spacing:0.08em; text-transform:uppercase; color:var(--vs-primary);
  background:var(--vs-primary-muted); border-radius:var(--vs-r-sm);
  padding:3px 10px; margin-bottom:var(--vs-s2);
}
.vs-hero {
  background:linear-gradient(180deg,#FFFFFF 0%,#FBFAF6 100%);
  border:1px solid var(--vs-border-subtle); border-radius:var(--vs-r-lg);
  box-shadow:0 8px 24px rgba(26,29,26,0.09); padding:var(--vs-s6);
}
.vs-stats { display:flex; gap:var(--vs-s5); margin-top:var(--vs-s5); flex-wrap:wrap; }
.vs-stat { min-width:132px; }
.vs-stat-value { font-family:var(--vs-mono); font-size:26px; font-weight:600;
  color:var(--vs-primary); font-variant-numeric:tabular-nums; }
.vs-stat-label { font-family:var(--vs-sans); font-size:12px; color:var(--vs-text-secondary);
  text-transform:uppercase; letter-spacing:0.07em; margin-top:2px; }
.vs-stat-note { font-family:var(--vs-sans); font-size:11px; color:var(--vs-text-tertiary); }
.vs-card {
  background:var(--vs-bg-surface); border:1px solid var(--vs-border-subtle);
  border-radius:var(--vs-r-md); box-shadow:0 2px 8px rgba(26,29,26,0.07);
  padding:var(--vs-s5); margin-bottom:var(--vs-s5);
}
.vs-card-head { font-family:var(--vs-serif); font-size:20px; font-weight:600;
  color:var(--vs-text-primary); margin-bottom:var(--vs-s3);
  padding-bottom:var(--vs-s2); border-bottom:1px solid var(--vs-border-subtle); }
.vs-eyebrow { font-family:var(--vs-sans); font-size:11px; font-weight:600;
  letter-spacing:0.08em; text-transform:uppercase; color:var(--vs-text-tertiary); }
.vs-answer { font-family:var(--vs-serif); font-size:17px; line-height:1.65;
  color:var(--vs-text-primary); }
.vs-passage {
  font-family:var(--vs-mono); font-size:13.5px; line-height:1.7;
  background:var(--vs-bg-sunken); border-left:3px solid var(--vs-primary);
  border-radius:var(--vs-r-sm); padding:var(--vs-s4); color:var(--vs-text-primary);
  white-space:pre-wrap; word-break:break-word;
}
.vs-meta { color:var(--vs-text-secondary); font-family:var(--vs-sans); font-size:13px; }
.vs-chip {
  display:inline-flex; align-items:center; gap:6px; font-family:var(--vs-sans);
  font-size:12.5px; font-weight:600; border-radius:var(--vs-r-sm);
  padding:4px 11px; border:1px solid transparent; white-space:nowrap;
}
.vs-chip-verified { background:var(--vs-verified-bg); color:var(--vs-verified);
  border-color:#C7E0D1; }
.vs-chip-review { background:var(--vs-review-bg); color:var(--vs-review);
  border-color:#EBD9AE; }
.vs-chip-unsupported { background:var(--vs-unsupported-bg); color:var(--vs-unsupported);
  border-color:#EFC9C9; }
.vs-row { display:flex; gap:var(--vs-s4); padding:var(--vs-s3) 0;
  border-bottom:1px solid var(--vs-border-subtle); align-items:flex-start; }
.vs-row:last-child { border-bottom:none; }
.vs-kv { display:flex; justify-content:space-between; gap:var(--vs-s4);
  padding:6px 0; font-family:var(--vs-sans); font-size:13.5px; }
.vs-kv-key { color:var(--vs-text-secondary); }
.vs-kv-val { font-family:var(--vs-mono); color:var(--vs-text-primary);
  font-variant-numeric:tabular-nums; font-weight:600; }
.vs-note { font-family:var(--vs-sans); font-size:12.5px; color:var(--vs-text-secondary);
  line-height:1.55; margin-top:var(--vs-s3); }
.vs-warn { background:var(--vs-review-bg); border:1px solid #EBD9AE;
  border-radius:var(--vs-r-sm); padding:var(--vs-s3) var(--vs-s4);
  font-family:var(--vs-sans); font-size:13px; color:var(--vs-review); }
.vs-error { background:var(--vs-unsupported-bg); border:1px solid #EFC9C9;
  border-radius:var(--vs-r-sm); padding:var(--vs-s3) var(--vs-s4);
  font-family:var(--vs-sans); font-size:13px; color:var(--vs-unsupported); }
.vs-info { background:var(--vs-info-bg); border:1px solid #CFDDEE;
  border-radius:var(--vs-r-sm); padding:var(--vs-s3) var(--vs-s4);
  font-family:var(--vs-sans); font-size:13px; color:var(--vs-info); }
.vs-empty { text-align:center; padding:var(--vs-s7) var(--vs-s5);
  border:1px dashed var(--vs-border-strong); border-radius:var(--vs-r-md);
  background:var(--vs-bg-surface); }
.vs-empty-title { font-family:var(--vs-serif); font-size:18px;
  color:var(--vs-text-primary); margin-bottom:var(--vs-s2); }
.vs-upload { border:2px dashed var(--vs-border-strong); border-radius:var(--vs-r-lg);
  background:var(--vs-bg-surface); padding:var(--vs-s7) var(--vs-s5); text-align:center; }
.vs-upload-icon { font-size:30px; color:var(--vs-primary); }
.vs-upload-title { font-family:var(--vs-serif); font-size:19px;
  color:var(--vs-text-primary); margin:var(--vs-s3) 0 var(--vs-s2); }
.vs-upload-meta { font-family:var(--vs-sans); font-size:12.5px;
  color:var(--vs-text-secondary); line-height:1.7; }
.vs-nav-label { font-family:var(--vs-sans); font-size:11px; font-weight:600;
  letter-spacing:0.08em; text-transform:uppercase; color:var(--vs-text-tertiary);
  margin:var(--vs-s4) 0 var(--vs-s2); }
.vs-side-stat { font-family:var(--vs-sans); font-size:12.5px; color:var(--vs-text-secondary);
  display:flex; justify-content:space-between; padding:3px 0; }
.vs-side-val { font-family:var(--vs-mono); color:var(--vs-text-primary);
  font-variant-numeric:tabular-nums; }
.vs-footer { font-family:var(--vs-sans); font-size:11.5px; color:var(--vs-text-tertiary);
  border-top:1px solid var(--vs-border-subtle); padding-top:var(--vs-s3);
  margin-top:var(--vs-s6); display:flex; gap:var(--vs-s4); flex-wrap:wrap; }
.vs-marker-btn { font-family:var(--vs-mono); font-size:12px; background:var(--vs-primary-muted);
  color:var(--vs-primary); border:1px solid #C7E0D1; border-radius:var(--vs-r-sm);
  padding:2px 8px; margin:2px 4px 2px 0; cursor:pointer; }
.vs-marker-btn:focus { outline:2px solid var(--vs-focus); outline-offset:2px; }
.vs-claim-card { border:1px solid var(--vs-border-subtle); border-radius:var(--vs-r-md);
  padding:var(--vs-s4); margin-bottom:var(--vs-s3); background:var(--vs-bg-surface); }
.vs-claim-text { font-family:var(--vs-serif); font-size:15px; color:var(--vs-text-primary);
  margin-bottom:var(--vs-s2); line-height:1.55; }
.vs-legend { font-family:var(--vs-sans); font-size:12px; color:var(--vs-text-tertiary);
  margin-top:var(--vs-s4); line-height:1.6; }
@media (prefers-reduced-motion: reduce) {
  .vs-card, .vs-hero, .vs-marker-btn { transition:none !important; animation:none !important; }
}
@media (max-width: 1199px) { .vs-stats { gap:var(--vs-s4); } }
@media (max-width: 767px) {
  .vs-card, .vs-hero { padding:var(--vs-s4); }
  .vs-row { flex-direction:column; gap:var(--vs-s2); }
  .vs-stat-value { font-size:22px; }
}
</style>
"""


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def get_pipeline() -> ResearchPipeline:
    """One pipeline per server process, cached.

    ``cache_resource`` rather than ``cache_data`` because the pipeline owns mutable state and an
    index. Reloading it per rerun would re-fit the TF-IDF vocabulary on every keystroke and throw away
    the user's collection. Rebuilding it is a deliberate button press, not a rerun.
    """
    return ResearchPipeline(
        PipelineConfig(embedding_backend="tfidf", store="memory")
    )


def _reset_pipeline() -> None:
    get_pipeline.clear()


def _init_state() -> None:
    st.session_state.setdefault("nav", "Dashboard")
    st.session_state.setdefault("question", "")
    st.session_state.setdefault("last_answer", None)
    st.session_state.setdefault("selected", None)
    st.session_state.setdefault("last_report", None)


def _markers_of(answer: AnswerResponse) -> list[tuple[str, str]]:
    """Every distinct ``(marker, claim_id)`` in the answer, in order of appearance."""
    seen: list[tuple[str, str]] = []
    for claim in answer.answer.claims:
        for ref in claim.markers:
            entry = (ref.raw, claim.claim_id)
            if entry not in seen:
                seen.append(entry)
    return seen


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------


def render_sidebar(pipeline: ResearchPipeline) -> str:
    stats = pipeline.index_stats()
    with st.sidebar:
        st.markdown(
            f'<div class="vs-nav-label">{escape(BRAND)}</div>'
            f'<div style="font-family:var(--vs-serif);font-size:19px;color:var(--vs-primary);">'
            f"{escape(TAGLINE.split('—')[0].strip())}</div>",
            unsafe_allow_html=True,
        )
        nav = st.radio(
            "Navigate",
            ["Dashboard", "Library", "Workspace"],
            key="nav",
            label_visibility="collapsed",
        )

        st.markdown('<div class="vs-nav-label">Index status</div>', unsafe_allow_html=True)
        # Live counts only. When the index is empty these read 0, which is the truth.
        rows = [
            ("Backend", stats.backend),
            ("Store", stats.store),
            ("Documents", f"{stats.document_count}"),
            ("Pages", f"{stats.total_pages}"),
            ("Chunks", f"{stats.total_chunks}"),
        ]
        for key, value in rows:
            st.markdown(
                f'<div class="vs-side-stat"><span>{escape(key)}</span>'
                f'<span class="vs-side-val">{escape(value)}</span></div>',
                unsafe_allow_html=True,
            )
        if stats.persist_path:
            st.markdown(
                f'<div class="vs-note" style="font-size:11.5px;">'
                f"Persisted at <code>{escape(stats.persist_path)}</code></div>",
                unsafe_allow_html=True,
            )
        if pipeline.restored_chunks:
            st.markdown(
                f'<div class="vs-info" style="font-size:11.5px;">Reused '
                f"{escape(pipeline.restored_chunks)} chunks from a persisted index.</div>",
                unsafe_allow_html=True,
            )

        st.markdown('<div class="vs-nav-label">Settings</div>', unsafe_allow_html=True)
        chunk_words = st.slider(
            "Chunk size (words)", 60, 400, pipeline.config.chunk.chunk_words, step=20,
            help="Target words per chunk. 180 fits MiniLM's 256-token window.",
        )
        overlap_words = st.slider(
            "Overlap (words)", 0, 120, pipeline.config.chunk.overlap_words, step=10,
            help="Words shared by consecutive chunks. Must be smaller than the chunk size.",
        )
        top_k = st.slider("Passages to retrieve", 1, 15, pipeline.config.top_k)
        verified = st.slider(
            "Verified threshold", 0.30, 0.95,
            float(pipeline.config.verification.verified_threshold), step=0.01,
        )
        review = st.slider(
            "Needs Review threshold", 0.05, 0.90,
            float(pipeline.config.verification.review_threshold), step=0.01,
        )
        max_upload = st.slider(
            "Max upload size (MB)", 1, 200, pipeline.config.limits.max_upload_mb
        )
        max_pages = st.slider(
            "Max pages per document", 5, 500, pipeline.config.limits.max_pages_per_document, step=5
        )

        if overlap_words >= chunk_words:
            st.markdown(
                f'<div class="vs-error">Overlap must be smaller than the chunk size. '
                f"An overlap of {escape(overlap_words)} with chunks of {escape(chunk_words)} "
                f"cannot advance.</div>",
                unsafe_allow_html=True,
            )
        elif review >= verified:
            st.markdown(
                '<div class="vs-error">Needs Review threshold must be below the Verified '
                f"threshold. Currently {escape(round(review, 2))} vs "
                f"{escape(round(verified, 2))}.</div>",
                unsafe_allow_html=True,
            )
        else:
            candidate = PipelineConfig(
                chunk=ChunkConfig(chunk_words=chunk_words, overlap_words=overlap_words),
                top_k=top_k,
                verification=replace(
                    pipeline.config.verification,
                    verified_threshold=verified,
                    review_threshold=review,
                ),
                limits=ResourceLimits(
                    max_upload_mb=max_upload, max_pages_per_document=max_pages
                ),
            )
            if candidate != pipeline.config:
                pipeline.reconfigure(candidate)

        st.markdown('<div class="vs-nav-label">Session</div>', unsafe_allow_html=True)
        if st.button("Clear the index", use_container_width=True):
            _reset_pipeline()
            st.session_state["last_answer"] = None
            st.session_state["selected"] = None
            st.rerun()
    return nav


# --------------------------------------------------------------------------
# Shared pieces
# --------------------------------------------------------------------------


def render_header() -> None:
    st.markdown(
        f'<div class="vs-header"><span class="vs-mark">▮</span>'
        f'<span class="vs-brand">{escape(BRAND)}</span>'
        f'<div class="vs-tagline">{escape(TAGLINE)}</div>'
        f'<div class="vs-badge" style="margin-top:12px;">'
        f"local-only · no API keys · v{escape(APP_VERSION)}</div></div>",
        unsafe_allow_html=True,
    )


def render_footer(pipeline: ResearchPipeline) -> None:
    """The active profile, stated plainly. A degraded run must not look like a full one."""
    stats = pipeline.index_stats()
    parts = [
        f"backend {stats.backend}",
        f"store {stats.store}",
        f"generator {pipeline.config.generator}",
        f"profile {'degraded' if pipeline.degraded_reason else 'offline'}",
    ]
    if pipeline.degraded_reason:
        parts.append(pipeline.degraded_reason)
    st.markdown(
        '<div class="vs-footer">'
        + "<span>·</span>".join(f"<span>{escape(part)}</span>" for part in parts)
        + "</div>",
        unsafe_allow_html=True,
    )


def chip(label: str) -> str:
    """A status chip. Colour **+** icon **+** text, always.

    The icon and the word are what carry the meaning; colour is supplementary. FR-45 — roughly 8% of
    men have some colour-vision deficiency, and this chip carries the project's actual finding.
    """
    modifier = {
        "Verified": "vs-chip-verified",
        "Needs Review": "vs-chip-review",
        "Unsupported": "vs-chip-unsupported",
    }.get(label, "vs-chip-review")
    return (
        f'<span class="vs-chip {modifier}"><span aria-hidden="true">'
        f"{escape(LABEL_ICON.get(label, '•'))}</span>{escape(label)}</span>"
    )


def show_failures(failures: Sequence[IngestFailure]) -> None:
    """Every rejected file, with its real reason and what to do next."""
    for failure in failures:
        recovery = RECOVERY.get(failure.reason, "Remove the file and try another.")
        st.markdown(
            f'<div class="vs-error"><strong>{escape(failure.filename)}</strong> — '
            f"{escape(failure.message)}<br><em>Next: {escape(recovery)}</em></div>",
            unsafe_allow_html=True,
        )


def show_warnings(warnings: Sequence[str]) -> None:
    for warning in warnings:
        st.markdown(f'<div class="vs-warn">{escape(warning)}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Surface 1 — Dashboard
# --------------------------------------------------------------------------


def render_dashboard(pipeline: ResearchPipeline) -> None:
    stats = pipeline.index_stats()
    limits = pipeline.config.limits

    tiles = [
        (f"{stats.document_count}", "Documents"),
        (f"{stats.total_pages}", "Pages"),
        (f"{stats.total_chunks}", "Chunks"),
    ]
    tile_html = "".join(
        f'<div class="vs-stat"><div class="vs-stat-value">{escape(value)}</div>'
        f'<div class="vs-stat-label">{escape(label)}</div></div>'
        for value, label in tiles
    )
    note = "live from the index" if stats.total_chunks else "nothing indexed yet"
    st.markdown(
        f'<div class="vs-hero"><div class="vs-eyebrow">Local research workspace</div>'
        f'<div class="vs-answer" style="margin:8px 0 4px;">'
        f"Every claim is compared against the exact page it cites.</div>"
        f'<div class="vs-stats">{tile_html}</div>'
        f'<div class="vs-stat-note" style="margin-top:10px;">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="vs-card"><div class="vs-card-head">Upload</div>', unsafe_allow_html=True)
    uploads = st.file_uploader(
        "Drop academic PDFs here, or browse",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="uploader",
    )
    st.markdown(
        f'<div class="vs-upload"><div class="vs-upload-icon">⬆</div>'
        f'<div class="vs-upload-title">Drop academic PDFs here, or use the picker above</div>'
        f'<div class="vs-upload-meta">PDF only · up to {escape(limits.max_upload_mb)} MB per file · '
        f"up to {escape(limits.max_pages_per_document)} pages per document<br>"
        "Scanned or image-only PDFs are not supported — there is no OCR in this project.</div></div>",
        unsafe_allow_html=True,
    )

    if uploads:
        _handle_uploads(pipeline, uploads)
    st.markdown("</div>", unsafe_allow_html=True)

    if pipeline.failures:
        st.markdown('<div class="vs-card"><div class="vs-card-head">Not indexed</div>',
                    unsafe_allow_html=True)
        show_failures(pipeline.failures)
        st.markdown("</div>", unsafe_allow_html=True)

    if pipeline.warnings:
        st.markdown('<div class="vs-card"><div class="vs-card-head">Notes</div>',
                    unsafe_allow_html=True)
        show_warnings(pipeline.warnings)
        st.markdown("</div>", unsafe_allow_html=True)

    if stats.total_chunks == 0:
        st.markdown(
            '<div class="vs-empty"><div class="vs-empty-title">No documents yet</div>'
            '<div class="vs-note">Upload a text-based PDF above. Every figure on this page reads '
            "from the live index, so nothing is shown until something is actually indexed.</div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="vs-card"><div class="vs-eyebrow">Next</div>'
            '<div class="vs-note" style="margin-top:6px;">'
            f"{escape(stats.document_count)} document(s) ready. Open the Workspace to ask a "
            "question and inspect the passages behind the answer.</div></div>",
            unsafe_allow_html=True,
        )


def _handle_uploads(pipeline: ResearchPipeline, uploads) -> None:
    """Stage the uploads on disk, index them, and record where each landed.

    Streamlit hands over file *contents*, not paths, and `pipeline.index` takes paths -- so the
    bytes are written to a per-session temp directory first. The source_id -> path map is kept in
    session state because the library's Reindex action needs the original file, and the pipeline
    deliberately does not retain paths (SEC-07: an absolute path must never leak into an ID or a UI
    element).
    """
    import tempfile

    staged: list[Path] = []
    staged_map: dict[str, str] = st.session_state.get("staged_paths") or {}
    with st.status("Uploading", expanded=True) as status:
        for upload in uploads:
            status.write(f"Reading {upload.name}")
            target = Path(tempfile.mkdtemp(prefix="vs_upload_")) / upload.name
            target.write_bytes(upload.getvalue())
            staged.append(target)

        status.update(label="Parsing and indexing", expanded=True)
        report = pipeline.index(staged)

        for document in report.documents:
            for path in staged:
                if path.name == document.display_name:
                    staged_map[document.source_id] = str(path)
        st.session_state["staged_paths"] = staged_map
        st.session_state["last_report"] = report

    if report.documents:
        status.update(label="Indexed", state="complete", expanded=False)
    else:
        status.update(label="Nothing was indexed", state="error", expanded=True)
        st.error("No file could be indexed. The reason for each is below.")


# --------------------------------------------------------------------------
# Surface 2 — Document library
# --------------------------------------------------------------------------


def render_library(pipeline: ResearchPipeline) -> None:
    stats = pipeline.index_stats()
    st.markdown('<div class="vs-card-head">Document library</div>', unsafe_allow_html=True)

    if stats.document_count == 0 and not pipeline.failures:
        st.markdown(
            '<div class="vs-empty"><div class="vs-empty-title">Nothing indexed</div>'
            '<div class="vs-note">Upload a PDF from the Dashboard to see it here. No placeholder '
            "rows are shown for documents that do not exist.</div></div>",
            unsafe_allow_html=True,
        )
        return

    rows = []
    for document in stats.documents:
        rows.append(
            {
                "Status": "Indexed",
                "Filename": document.display_name,
                "Pages": document.page_count,
                "Chunks": document.chunk_count,
                "Engine": "Semantic" if document.engine == "minilm" else "Lexical",
                "Source ID": document.source_id,
            }
        )
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)

    if pipeline.failures:
        st.markdown('<div class="vs-card-head" style="margin-top:24px;">Failed</div>',
                    unsafe_allow_html=True)
        show_failures(pipeline.failures)

    if pipeline.warnings:
        st.markdown('<div class="vs-card-head" style="margin-top:24px;">Warnings</div>',
                    unsafe_allow_html=True)
        show_warnings(pipeline.warnings)

    st.markdown('<div class="vs-card-head" style="margin-top:24px;">Manage</div>',
                unsafe_allow_html=True)
    if rows:
        chosen = st.selectbox(
            "Choose a document", [r["Source ID"] for r in rows],
            format_func=lambda sid: next(r["Filename"] for r in rows if r["Source ID"] == sid),
            label_visibility="collapsed",
        )
        column_a, column_b = st.columns(2)
        with column_a:
            if st.button("Remove from index", use_container_width=True, key="remove_doc"):
                st.session_state["confirm_remove"] = chosen
                st.rerun()
        with column_b:
            if st.button("Reindex", use_container_width=True, key="reindex_doc"):
                try:
                    path = _source_path(pipeline, chosen)
                except FileNotFoundError:
                    st.warning(
                        "This document was not uploaded in this session, so its file is not "
                        "available to re-read. Upload it again from the Dashboard; indexing is "
                        "idempotent, so re-uploading replaces rather than duplicates it."
                    )
                else:
                    with st.spinner("Reindexing…"):
                        pipeline.reindex_document(path)
                    st.session_state["last_answer"] = None
                    st.rerun()

        if st.session_state.get("confirm_remove") == chosen:
            st.markdown(
                '<div class="vs-warn">Removing a document deletes its chunks from the index. '
                "Uploading the file again will rebuild them.</div>",
                unsafe_allow_html=True,
            )
            yes, no = st.columns(2)
            with yes:
                if st.button("Yes, remove it", use_container_width=True, key="confirm_yes"):
                    pipeline.remove_document(chosen)
                    st.session_state.pop("confirm_remove", None)
                    st.session_state["last_answer"] = None
                    st.rerun()
            with no:
                if st.button("Keep it", use_container_width=True, key="confirm_no"):
                    st.session_state.pop("confirm_remove", None)
                    st.rerun()


def _source_path(pipeline: ResearchPipeline, source_id: str) -> Path:
    """The staged file for a source id, or `FileNotFoundError` if it is not in this session.

    The pipeline keeps counts, not paths, by design: SEC-07 keeps writes inside the project and an
    absolute path must never leak into an ID or a UI element. The consequence is that reindex needs
    the original file, so the UI keeps a session-local map from `source_id` to the temp path it
    staged, and says so plainly when a document predates the session.
    """
    staged = st.session_state.get("staged_paths") or {}
    path = staged.get(source_id)
    if path and Path(path).exists():
        return Path(path)
    raise FileNotFoundError(source_id)


# --------------------------------------------------------------------------
# Surface 3 — Research workspace
# --------------------------------------------------------------------------


def render_workspace(pipeline: ResearchPipeline) -> None:
    stats = pipeline.index_stats()
    st.markdown('<div class="vs-card-head">Research workspace</div>', unsafe_allow_html=True)

    if stats.total_chunks == 0:
        st.markdown(
            '<div class="vs-empty"><div class="vs-empty-title">The index is empty</div>'
            '<div class="vs-note">Upload a text-based PDF from the Dashboard first. Asking a '
            "question against nothing would produce an answer with no evidence behind it, which is "
            "the one outcome this project exists to prevent.</div></div>",
            unsafe_allow_html=True,
        )
        return

    form_left, form_right = st.columns([5, 1])
    with form_left:
        question = st.text_input(
            "Ask a question", key="question",
            placeholder="What technology stack does the report specify?",
            label_visibility="collapsed",
        )
    with form_right:
        asked = st.button("Ask", type="primary", use_container_width=True)

    if asked:
        if not question.strip():
            # EC-05 refuses a blank question before any retrieval happens. The UI says so
            # rather than letting the button appear to do nothing.
            st.warning("Enter a question first. A blank question is rejected before retrieval.")
            return
        with st.spinner("Retrieving passages…"):
            try:
                response = pipeline.ask(question.strip())
            except ValueError as exc:
                st.error(str(exc))
                return
        st.session_state["last_answer"] = response
        st.session_state["selected"] = None
    else:
        response = st.session_state.get("last_answer")

    if response is None:
        st.markdown(
            '<div class="vs-note">Ask a question to see an answer with page-level citations, '
            "then open any citation to read the passage it points at.</div>",
            unsafe_allow_html=True,
        )
        return

    _render_answer(response)
    _render_verification(response)
    _render_inspector(response)
    _render_retrieved(response)


def _render_answer(response: AnswerResponse) -> None:
    st.markdown('<div class="vs-card-head">Answer</div>', unsafe_allow_html=True)
    if response.answer.abstained:
        st.markdown(
            '<div class="vs-info"><strong>No answer was produced.</strong> The retrieved evidence '
            "was insufficient, so the system declined rather than answering from memory. "
            'Add documents, or rephrase to match the document language.</div>',
            unsafe_allow_html=True,
        )
        return
    if response.answer.degraded:
        st.markdown(
            '<div class="vs-warn">Running in degraded mode. The answer came from the fallback '
            "generator, not the configured one.</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="vs-card"><div class="vs-answer">{escape(response.answer.text)}</div></div>',
        unsafe_allow_html=True,
    )

    markers = _markers_of(response)
    if markers:
        st.markdown(
            '<div class="vs-legend">Citations in this answer. Select one below to open the '
            "passage it points at:</div>",
            unsafe_allow_html=True,
        )

    columns = st.columns(len(markers) or 1)
    for column, (raw, claim_id) in zip(columns, markers, strict=False):
        with column:
            if st.button(raw, key=f"marker_{claim_id}_{raw}", use_container_width=True):
                st.session_state["selected"] = claim_id
                st.rerun()


def _render_verification(response: AnswerResponse) -> None:
    summary = response.summary
    st.markdown('<div class="vs-card-head">Verification</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="vs-note" style="margin-top:0;">{escape(summary.headline)}</div>',
        unsafe_allow_html=True,
    )

    counts = {
        "Verified": summary.verified,
        "Needs Review": summary.needs_review,
        "Unsupported": summary.unsupported,
    }
    columns = st.columns(3)
    for column, label in zip(columns, VERIFICATION_LABELS, strict=True):
        with column:
            st.markdown(
                f'<div class="vs-card" style="margin-bottom:12px;">{chip(label)}'
                f'<div style="font-family:var(--vs-mono);font-size:22px;font-weight:600;'
                f'margin-top:10px;color:var(--vs-text-primary);">{escape(counts[label])}</div>'
                f'<div class="vs-note" style="margin-top:6px;">'
                f"{escape(LABEL_MEANING[label])}</div></div>",
                unsafe_allow_html=True,
            )

    if not response.verifications:
        st.markdown(
            '<div class="vs-info">Nothing to verify — the answer was abstained on.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="vs-card"><div class="vs-eyebrow">Claim by claim</div>', unsafe_allow_html=True)
    for verification in response.verifications:
        st.markdown(
            f'<div class="vs-claim-card">{chip(verification.label)}'
            f'<div class="vs-claim-text" style="margin-top:10px;">'
            f"{escape(verification.claim_text)}</div>"
            f'<div class="vs-kv"><span class="vs-kv-key">support</span>'
            f'<span class="vs-kv-val">{escape(f"{verification.support_score:.2f}")}</span></div>'
            f'<div class="vs-note">{escape(verification.explanation)}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="vs-legend">Support scores measure how closely a claim matches the passage it '
        "cites. They are not proof that a claim is true, and they are not the same number as the "
        "retrieval relevance shown in the evidence inspector.</div></div>",
        unsafe_allow_html=True,
    )


def _render_inspector(response: AnswerResponse) -> None:
    selected = st.session_state.get("selected")
    st.markdown('<div class="vs-card-head">Evidence inspector</div>', unsafe_allow_html=True)

    verification = next(
        (v for v in response.verifications if v.claim_id == selected), None
    )
    if verification is None:
        verification = response.verifications[0] if response.verifications else None

    if verification is None:
        st.markdown(
            '<div class="vs-empty"><div class="vs-empty-title">No evidence to inspect</div>'
            '<div class="vs-note">The answer was abstained on, so there is no cited passage.</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        return

    evidence = verification.evidence
    header = f'<div class="vs-card"><div class="vs-card-head">Claim {escape(verification.claim_id)}</div>'
    header += f"{chip(verification.label)}</div>"

    if evidence is None:
        st.markdown(
            header
            + f'<div class="vs-note" style="margin-top:12px;">'
            f"{escape(verification.explanation)}</div>"
            + '<div class="vs-note">Because the citation could not be resolved, there is no passage '
            "to show. The system does not substitute a different passage for the one that was "
            "cited.</div></div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(header, unsafe_allow_html=True)
    st.markdown(
        f'<div class="vs-kv"><span class="vs-kv-key">{escape(evidence.filename)}</span>'
        f'<span class="vs-kv-val">page {escape(evidence.page_number)}</span></div>'
        f'<div class="vs-kv"><span class="vs-kv-key">support score</span>'
        f'<span class="vs-kv-val">{escape(f"{verification.support_score:.2f}")}</span></div>'
        f'<div class="vs-kv"><span class="vs-kv-key">similarity component</span>'
        f'<span class="vs-kv-val">{escape(f"{verification.similarity:.2f}")}</span></div>'
        f'<div class="vs-kv"><span class="vs-kv-key">token overlap component</span>'
        f'<span class="vs-kv-val">{escape(f"{verification.overlap:.2f}")}</span></div>'
        f'<div class="vs-kv"><span class="vs-kv-key">retrieval relevance to your question</span>'
        f'<span class="vs-kv-val">'
        f"{escape('n/a' if verification.relevance_score is None else f'{verification.relevance_score:.2f}')}"
        "</span></div>"
        f'<div class="vs-kv"><span class="vs-kv-key">reason</span>'
        f'<span class="vs-kv-val">{escape(verification.reason)}</span></div>'
        f'<div class="vs-eyebrow" style="margin-top:18px;">Passage as retrieved</div>'
        f'<div class="vs-passage">{escape(evidence.text)}</div>'
        f'<div class="vs-note">{escape(REASON_TEXT.get(verification.reason, ""))}</div>'
        f'<div class="vs-note"><strong>What this label does not mean:</strong> '
        f"{escape(verification.explanation.split('. This means')[-1] if '. This means' in verification.explanation else 'It is a heuristic correspondence score, not proof that the claim is true.')}"
        "</div></div>",
        unsafe_allow_html=True,
    )


def _render_retrieved(response: AnswerResponse) -> None:
    if not response.retrieved:
        return
    st.markdown('<div class="vs-card-head">Passages retrieved</div>', unsafe_allow_html=True)
    rows = [
        {
            "Rank": result.rank,
            "Marker": f"S{result.rank}",
            "Page": result.chunk.page_number,
            "Document": result.chunk.filename,
            "Retrieval relevance": round(result.relevance_score, 3),
        }
        for result in response.retrieved
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown(
        '<div class="vs-legend">Retrieval relevance answers "is this passage about what I asked?" '
        'Claim support answers "does this passage support this sentence?". They are different '
        "questions and are never averaged.</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title=f"{BRAND} — Academic Research Assistant",
        page_icon="▮",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(STYLESHEET, unsafe_allow_html=True)
    _init_state()
    pipeline = get_pipeline()

    render_header()
    nav = render_sidebar(pipeline)

    if nav == "Dashboard":
        render_dashboard(pipeline)
    elif nav == "Library":
        render_library(pipeline)
    else:
        render_workspace(pipeline)

    render_footer(pipeline)


if __name__ == "__main__":
    main()
