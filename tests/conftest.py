"""Shared test fixtures.

Both test modules need real PDFs, so the builders live here rather than being duplicated.
`conftest.py` is loaded by pytest automatically and its helpers are exposed to tests as fixtures --
no test module imports anything from here, which keeps the fixture set honest about what a test
actually depends on.

`build_pdf` is a ~60-line PDF writer: catalog, page tree, one font, a text content stream per page,
a real cross-reference table and a real trailer. Hand-rolling it is worth it because no Python PDF
library can write text, because a committed 200 KB binary cannot be reviewed in a diff, and because
`graphics_only=True` produces the image-only page that makes the scanned-document test convincing.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter

from src.models import ChunkConfig, DocumentPage, PipelineConfig

# Topically distinctive page text. Retrieval tests are only meaningful if each page is about
# something different; the same sentence on every page would make any ranking score look plausible.
PAGE_TEXTS = [
    "Retrieval augmented generation grounds answers in external evidence.",
    "Cosine similarity measures relatedness between embedding vectors.",
    "Chunk overlap reduces the chance that a definition is split at a boundary.",
    "Chroma persists embeddings on the local filesystem without a database server.",
    "The verification threshold labels claims as verified or unsupported.",
]

SECOND_DOCUMENT_TEXTS = [
    "Evidence must resolve to a real page of a real document before a claim can be supported.",
]

LONG_PAGE_BODY = " ".join(
    f"Sentence number {i} describes retrieval augmented generation in academic PDFs."
    for i in range(120)
)


# The font in `build_pdf` declares `/WinAnsiEncoding`, which **is** Windows-1252. Encoding the
# content stream as ISO-8859-1 therefore mismatches the declaration, and every character that
# exists only in the 0x80-0x9F range -- em dash, curly quotes, en dash -- is replaced by `?` at
# *write* time. The extractor then faithfully returns the question marks it was given, which reads
# as an extraction failure when the fault is here.
#
# Found by building a fixture with non-ASCII content and checking the raw content-stream bytes
# rather than trusting the extracted text: the stream contained literal `?` (0x3F) where the em
# dash should have been. Accented characters survived precisely because they are in ISO-8859-1.
#
# cp1252 is the correct pairing and is a strict superset of latin-1 for the printable range, so
# ASCII-only fixtures are byte-identical either way.
_CONTENT_ENCODING = "cp1252"


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(page_texts: list[str], *, graphics_only: bool = False) -> bytes:
    """Build a minimal but genuinely valid PDF with one text line per source line."""
    page_count = len(page_texts)
    font_obj = 3
    page_ids = [4 + 2 * i for i in range(page_count)]
    content_ids = [5 + 2 * i for i in range(page_count)]

    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: (
            "<< /Type /Pages /Kids ["
            + " ".join(f"{pid} 0 R" for pid in page_ids)
            + f"] /Count {page_count} >>"
        ).encode("ascii"),
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    }

    for index, text in enumerate(page_texts):
        if graphics_only:
            # A filled rectangle: a page with marks on it and no text layer, which is
            # exactly what a scanner produces.
            body = "0.2 0.4 0.3 rg 72 200 400 300 re f"
        else:
            lines = text.split("\n")
            body = (
                "BT /F1 11 Tf 72 720 Td 14 TL\n"
                + "".join(f"({escape_pdf_text(line)}) Tj T*\n" for line in lines)
                + "ET"
            )
        stream = body.encode(_CONTENT_ENCODING, "replace")
        objects[page_ids[index]] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
            f"/Contents {content_ids[index]} 0 R >>"
        ).encode("ascii")
        objects[content_ids[index]] = (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: dict[int, int] = {}
    for number in sorted(objects):
        offsets[number] = len(out)
        out += f"{number} 0 obj\n".encode("ascii") + objects[number] + b"\nendobj\n"

    xref_at = len(out)
    size = max(objects) + 1
    out += f"xref\n0 {size}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for number in range(1, size):
        out += f"{offsets[number]:010d} 00000 n \n".encode("ascii")
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode(
        "ascii"
    )
    return bytes(out)


def encrypt_pdf(raw: bytes, password: str = "secret") -> bytes:
    """Wrap a built PDF in pypdf's encryption. Deterministic for a fixed input."""
    writer = PdfWriter(clone_from=BytesIO(raw))
    writer.encrypt(password)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def write_pdf(tmp_path: Path, name: str, payload: bytes) -> Path:
    target = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


@pytest.fixture
def page_factory():
    """Build a `DocumentPage` without going near the filesystem."""

    def make(source_id: str, page_number: int, text: str, filename: str = "unit.pdf"):
        return DocumentPage(
            source_id=source_id,
            filename=filename,
            display_name=filename,
            page_number=page_number,
            text=text,
            extractor="pypdf",
        )

    return make


@pytest.fixture
def chunk_config() -> ChunkConfig:
    return ChunkConfig()


EVIDENCE_TEXTS = [
    "Chunk overlap between consecutive passages reduces the chance that a definition is split at a chunk boundary.",
    "Chroma persists embeddings on the local filesystem without a database server.",
    "Cosine similarity measures relatedness between embedding vectors.",
    "Training on the dataset did not significantly improve accuracy.",
    "The verification threshold labels claims as verified or unsupported.",
]


@pytest.fixture
def evidence_pdf(tmp_path: Path) -> Path:
    """Five pages on distinct topics, shared by the verification and UI suites.

    One fixture rather than two: if the UI test indexed different text than the verifier tests, a UI
    result could look fine while the verification result underneath it was never exercised.
    """
    return write_pdf(tmp_path, "evidence.pdf", build_pdf(EVIDENCE_TEXTS))


# -- documents ------------------------------------------------------------


@pytest.fixture
def valid_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "valid_text.pdf", build_pdf(PAGE_TEXTS))


@pytest.fixture
def multi_page_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "multi_page.pdf", build_pdf(PAGE_TEXTS * 2))


@pytest.fixture
def other_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "second_document.pdf", build_pdf(SECOND_DOCUMENT_TEXTS))


@pytest.fixture
def long_page_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "long_page.pdf", build_pdf([LONG_PAGE_BODY]))


@pytest.fixture
def scanned_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "scanned.pdf", build_pdf(["", "", ""], graphics_only=True))


@pytest.fixture
def encrypted_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "encrypted.pdf", encrypt_pdf(build_pdf(PAGE_TEXTS[:1])))


@pytest.fixture
def empty_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "empty.pdf", b"")


@pytest.fixture
def corrupt_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "corrupt.pdf", b"%PDF-1.4\nthis is not a pdf body\n")


@pytest.fixture
def not_a_pdf(tmp_path: Path) -> Path:
    return write_pdf(tmp_path, "notes.txt", b"just some text, not a pdf")


@pytest.fixture
def many_page_pdf(tmp_path: Path) -> Path:
    """15 pages. SEC-03 names 5,000; the limit branch is identical at 1/333rd the build cost."""
    return write_pdf(tmp_path, "fifteen.pdf", build_pdf(PAGE_TEXTS * 3))


# -- pipeline configurations ----------------------------------------------


@pytest.fixture
def offline_config() -> PipelineConfig:
    """The default, guaranteed-offline profile: TF-IDF plus the in-memory store."""
    return PipelineConfig(embedding_backend="tfidf", store="memory")


@pytest.fixture
def make_config():
    def build(**overrides) -> PipelineConfig:
        base = {"embedding_backend": "tfidf", "store": "memory"}
        base.update(overrides)
        return PipelineConfig(**base)

    return build