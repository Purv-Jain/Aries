"""PDF validation and page-wise text extraction.

Responsibility, and nothing else: turn a path to an untrusted file into a tuple of
``DocumentPage``, or raise a ``PDFIngestionError`` that names the file and the
cause. Chunking, embedding and indexing are other modules' problems.

Design points that are deliberate:

* **Cheap checks first.** Extension, existence, size and page count are settled
  before any text is extracted, so a decompression bomb is refused before it can
  be expanded.
* **Two parsers, one winner per page.** ``pypdf`` is fast and good on ordinary
  text; ``pdfplumber`` reads multi-column and table layouts that ``pypdf`` often
  flattens into nonsense. The page with more usable text wins, per page.
* **No text anywhere is a distinct outcome.** A scanned PDF is not a corrupt PDF
  and not an empty file. It gets its own error naming OCR as the missing step,
  because "nothing found" without that explanation is indistinguishable from a bug.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from src.models import (
    USER_MESSAGES,
    DocumentPage,
    ResourceLimits,
    Reason,
    compute_source_id,
)

__all__ = [
    "PDFIngestionError",
    "UnsupportedFormatError",
    "MissingFileError",
    "EmptyPdfError",
    "EncryptedPdfError",
    "CorruptPdfError",
    "ScannedPdfError",
    "LimitExceededError",
    "FileTooLargeError",
    "TooManyPagesError",
    "sanitize_display_name",
    "detect_injection_patterns",
    "load_document",
    "NEAR_EMPTY_CHARS",
    "MAX_DISPLAY_NAME_CHARS",
]

# A page yielding fewer than this many non-space characters is treated as
# under-read and handed to pdfplumber before being accepted.
NEAR_EMPTY_CHARS = 20

MAX_DISPLAY_NAME_CHARS = 120

_FALLBACK_DISPLAY_NAME = "unnamed-document.pdf"

_WS_RUN = re.compile(r"\s+")
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")

# Shapes of instruction-like text that a PDF author can embed. Detection only --
# the text is always treated as evidence and never as an instruction (SEC-05,
# Architecture section 7). Flagging is what lets the UI warn the user.
_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ignore_previous_instructions",
        re.compile(r"\bignore\s+(?:all\s+|any\s+)?(?:the\s+|your\s+)?(?:previous|prior|above|earlier)\b", re.I),
    ),
    (
        "disregard_instructions",
        re.compile(r"\bdisregard\s+(?:all\s+|any\s+)?(?:the\s+|your\s+)?(?:previous|prior|above|earlier|instructions?)\b", re.I),
    ),
    ("role_override", re.compile(r"\byou\s+are\s+now\b", re.I)),
    ("citation_forcing", re.compile(r"\bmark\s+(?:every|all)\s+(?:citation|citations|claim|claims|reference|references)\b", re.I)),
    ("answer_forcing", re.compile(r"\balways\s+answer\b", re.I)),
    ("system_prompt_claim", re.compile(r"\bsystem\s+prompt\b", re.I)),
)


class PDFIngestionError(Exception):
    """Base class for every ingestion failure.

    Carries a stable ``reason`` code so the UI, the tests and the report can all
    branch on the same value instead of matching message text.
    """

    reason: str = Reason.CORRUPT_PDF

    def __init__(self, message: str | None = None, *, filename: str = "", cause: str | None = None) -> None:
        self.filename = filename
        self.cause = cause
        resolved = message or USER_MESSAGES.get(self.reason, "That file could not be processed.")
        super().__init__(resolved)
        self.message = resolved


class MissingFileError(PDFIngestionError):
    reason = Reason.FILE_NOT_FOUND


class UnsupportedFormatError(PDFIngestionError):
    reason = Reason.UNSUPPORTED_EXTENSION


class EmptyPdfError(PDFIngestionError):
    reason = Reason.EMPTY_FILE


class EncryptedPdfError(PDFIngestionError):
    reason = Reason.ENCRYPTED_PDF


class CorruptPdfError(PDFIngestionError):
    reason = Reason.CORRUPT_PDF


class ScannedPdfError(PDFIngestionError):
    reason = Reason.SCANNED_PDF


class LimitExceededError(PDFIngestionError):
    """Base class for the two resource ceilings, so callers can catch one type."""

    reason = Reason.TOO_LARGE


class FileTooLargeError(LimitExceededError):
    reason = Reason.TOO_LARGE


class TooManyPagesError(LimitExceededError):
    reason = Reason.TOO_MANY_PAGES


def sanitize_display_name(filename: str) -> str:
    """Reduce an untrusted upload name to something safe to render.

    Only ever the *display* name is sanitised; ``filename`` keeps the original so
    the user recognises their own file. Steps are ordered deliberately: strip the
    directory component first, because that is what defeats traversal, and strip
    leading dots afterwards, because ``..`` survives ``os.path.basename``.
    """
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    base = _CONTROL_CHARS.sub("_", base)
    base = base.replace("/", "_").replace(":", "_")
    base = _WS_RUN.sub(" ", base).strip()
    base = base.lstrip(".").strip()
    if len(base) > MAX_DISPLAY_NAME_CHARS:
        stem, dot, ext = base.rpartition(".")
        if dot and len(ext) <= 12:
            keep = MAX_DISPLAY_NAME_CHARS - len(ext) - 1
            base = stem[: max(keep, 1)] + "." + ext
        else:
            base = base[:MAX_DISPLAY_NAME_CHARS]
    if not base.strip("._-") or base in {".", ".."}:
        return _FALLBACK_DISPLAY_NAME
    return base


def detect_injection_patterns(text: str) -> tuple[str, ...]:
    """Return the codes of any instruction-like patterns found in untrusted text.

    This never removes or rewrites the text -- the sentence still gets indexed and
    still gets quoted. The point is that the UI can say "this document contains
    instruction-like text" instead of leaving the user to discover it.
    """
    found: list[str] = []
    for code, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            found.append(code)
    return tuple(found)


def _normalise_text(raw: str | None) -> str:
    return _WS_RUN.sub(" ", raw or "").strip()


def _extract_page_texts_pypdf(reader: PdfReader, page_count: int) -> list[str]:
    texts: list[str] = []
    for index in range(page_count):
        try:
            page = reader.pages[index]
            texts.append(_normalise_text(page.extract_text()))
        except Exception:
            # One unreadable page must not discard the rest of the document.
            # pdfplumber gets a chance below; if it also fails the page stays empty
            # and is reported rather than hidden.
            texts.append("")
    return texts


def _extract_page_texts_pdfplumber(pdf_path: Path, wanted: set[int]) -> dict[int, str]:
    """Extract the given page indices in a single open.

    Opening the file once per page would make ingestion quadratic in page count on
    exactly the large documents the page limit is meant to bound.
    """
    if not wanted:
        return {}
    out: dict[int, str] = {}
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            total = len(pdf.pages)
            for index in sorted(wanted):
                if 0 <= index < total:
                    out[index] = _normalise_text(pdf.pages[index].extract_text())
    except Exception:
        # pdfplumber is a fallback, not a gate. If it cannot open the file at all,
        # pypdf's result stands and the page is reported as low-text.
        return out
    return out


def _validate(pdf_path: Path, limits: ResourceLimits) -> tuple[int, PdfReader]:
    """Run every check that does not require text extraction.

    Returns the page count and an open ``PdfReader``. Ordering matters: existence,
    extension and size are decided before the file is parsed at all, and the page
    count is taken from the document structure rather than from extracted text.
    """
    if not pdf_path.exists():
        raise MissingFileError(filename=pdf_path.name)

    if pdf_path.suffix.lower() != ".pdf":
        raise UnsupportedFormatError(filename=pdf_path.name)

    size_bytes = pdf_path.stat().st_size
    if size_bytes == 0:
        raise EmptyPdfError(filename=pdf_path.name)
    if size_bytes > limits.max_upload_bytes:
        raise FileTooLargeError(
            f"That file is {size_bytes / (1024 * 1024):.1f} MB, above the configured "
            f"limit of {limits.max_upload_mb} MB.",
            filename=pdf_path.name,
        )

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise CorruptPdfError(
            filename=pdf_path.name, cause=f"{type(exc).__name__}: {exc}"
        ) from exc

    if reader.is_encrypted:
        raise EncryptedPdfError(filename=pdf_path.name)

    page_count = len(reader.pages)
    if page_count == 0:
        raise EmptyPdfError("That PDF contains no pages.", filename=pdf_path.name)
    if page_count > limits.max_pages_per_document:
        raise TooManyPagesError(
            f"That document has {page_count} pages, above the configured limit of "
            f"{limits.max_pages_per_document}.",
            filename=pdf_path.name,
        )

    return page_count, reader


def load_document(
    path: str | os.PathLike[str],
    limits: ResourceLimits | None = None,
) -> tuple[DocumentPage, ...]:
    """Validate one PDF and extract it page by page.

    Returns a 1-based, gap-free tuple of ``DocumentPage``. Raises
    ``PDFIngestionError`` for every user-facing failure; a page that both parsers
    under-read is reported as a low-text warning rather than silently accepted as
    empty.
    """
    limits = limits or ResourceLimits()
    pdf_path = Path(path)
    display_name = sanitize_display_name(pdf_path.name)

    page_count, reader = _validate(pdf_path, limits)
    size_bytes = pdf_path.stat().st_size
    source_id = compute_source_id(pdf_path.name, size_bytes, page_count)

    texts = _extract_page_texts_pypdf(reader, page_count)
    del reader

    wanted = {i for i, text in enumerate(texts) if len(text) < NEAR_EMPTY_CHARS}
    fallbacks = _extract_page_texts_pdfplumber(pdf_path, wanted)

    pages: list[DocumentPage] = []
    for index in range(page_count):
        text = texts[index]
        warnings: list[str] = []

        if len(text) < NEAR_EMPTY_CHARS:
            fallback_text = fallbacks.get(index, "")
            if len(fallback_text) > len(text):
                text = fallback_text
                extractor = "pdfplumber"
                warnings.append("pdfplumber_fallback_used")
            else:
                extractor = "none"
                warnings.append("low_text_page")
        else:
            extractor = "pypdf"

        injection_codes = detect_injection_patterns(text)
        for code in injection_codes:
            warnings.append(f"injection_pattern_detected:{code}")

        pages.append(
            DocumentPage(
                source_id=source_id,
                filename=pdf_path.name,
                display_name=display_name,
                page_number=index + 1,
                text=text,
                extractor=extractor,
                warnings=tuple(warnings),
            )
        )

    if all(len(page.text) < NEAR_EMPTY_CHARS for page in pages):
        raise ScannedPdfError(filename=pdf_path.name)

    return tuple(pages)