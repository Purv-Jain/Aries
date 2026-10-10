"""Generate the synthetic report corpus used to test generality.

**Why this exists.** Every measurement in this project until now was taken against one document:
the team's own 15-page Stage 2 report. That is a real report, and it is the right thing to calibrate
on, but it is *one* document. A system that only works on it has not been shown to work on a report
nobody in this room has read.

So this script builds PDFs whose **layout and typography differ deliberately**, each carrying
technical prose that is factually independent of the Stage 2 report. Every one is synthesised here
from literal strings: no team names, no PRNs, no institutional identifiers, nothing taken from
anyone else's document.

The point is not to prove the system handles "every research report". That is not a claim anyone
can make from a finite test set. The point is to show it survives a **documented range of real
extraction hazards**, and to say plainly which hazards are covered and which are not.

Layouts covered
---------------
``two_column``      two text columns, the classic case where naive extraction interleaves lines
``single_column``   the ordinary case, as a control
``wide_table``      space-padded table rows, so extraction yields runs of whitespace
``long_page``       a page far longer than any normal one, to exercise chunk boundaries
``hyphenated``      words broken across lines with a hyphen, the other classic failure
``unicode``         non-ASCII text: an em dash, an accented word, a curly quote
``headers_footers`` a running head and page number on every page, which must not pollute answers
``scanned``         graphics only, no text layer: what a scanner produces
``encrypted``       password protected, which must be refused with a readable reason

Every byte is a pure function of the source, so re-running this script is idempotent.

    .venv\\Scripts\\python.exe -X utf8 tools\\build_fixtures.py

Writes into ``tests/data/fixtures/``. **All nine are committed**, at roughly 36 KB in total, so
that `pytest -q` on a fresh clone runs the generality suite with nothing to build first. A test
that needs a generator run before it can pass is a test a fresh clone will not have run.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.conftest import build_pdf, encrypt_pdf  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = PROJECT_ROOT / "tests" / "data" / "fixtures"

# Named so `main` can report which one a caller should expect first. All layouts are committed.
COMMITTED = "single_column"  # builder name, not the filename


def _paragraphs(topic_sentences: list[str], *, repeats: int = 1) -> list[str]:
    lines = []
    for _ in range(repeats):
        lines.extend(topic_sentences)
    return lines


# -- layout builders -------------------------------------------------------
#
# Each returns a list of page texts. The *content* is intentionally similar across layouts so a
# comparison between two layouts isolates the layout rather than the subject matter.


def _content(*, pages: int = 4) -> list[list[str]]:
    """`pages` pages of technical prose about a fictional instrument."""
    page_topics = [
        [
            "3.1 Calibration Procedure",
            "The spectrometer was calibrated against a reference lamp before each session.",
            "Calibration coefficients are stored alongside the raw readings, never inside them.",
            "A drifted calibration is detected by comparing the reference lamp response to its",
            "recorded baseline, and a drift above two percent triggers a full recalibration.",
        ],
        [
            "4.2 Sampling Strategy",
            "Samples were drawn every ninety seconds over a six hour acquisition window.",
            "The sampler discards the first reading of each window as a settling artefact.",
            "Drift correction is applied before the samples are averaged, not afterwards.",
            "Averaging first would fold the drift into every mean and hide the correction.",
        ],
        [
            "5.1 Noise Characteristics",
            "Thermal noise dominates below the detector's threshold and cannot be calibrated away.",
            "Shot noise scales with the square root of the exposure time at low flux.",
            "Both sources are reported separately rather than combined into one figure.",
            "Combining them would hide which one dominates under the conditions that matter.",
        ],
        [
            "6.3 Reproducibility Statement",
            "Every figure in this report was produced by the pipeline committed alongside it.",
            "No number in this report was transcribed by hand from a previous version.",
            "The deterministic profile requires no network access and no downloaded weights.",
            "The same input therefore yields the same output on any machine that runs the code.",
        ],
    ]
    while len(page_topics) < pages:
        page_topics.append(
            [
                f"Appendix {len(page_topics) + 1}. Additional Measurements",
                "Additional readings were collected under the conditions described above.",
                "The acquisition parameters were unchanged between sessions.",
            ]
        )
    return page_topics[:pages]


def build_single_column(pages: int = 4) -> bytes:
    return build_pdf(["\n".join(page) for page in _content(pages=pages)])


def build_two_column(pages: int = 4) -> bytes:
    """Two columns per page, placed side by side.

    Built as a raw content stream rather than through the single-column helper, because the whole
    point is the geometry: a naive extractor reads down the left column and then the right, which
    is correct, or alternates by y-coordinate, which is not. The second column continues the topic
    so a reader has no cue that the columns were split.
    """
    from tests.conftest import escape_pdf_text

    topics = _content(pages=pages)
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: (
            "<< /Type /Pages /Kids ["
            + " ".join(f"{4 + 2 * i} 0 R" for i in range(len(topics)))
            + f"] /Count {len(topics)} >>"
        ).encode("ascii"),
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    }
    for index, lines in enumerate(topics):
        half = (len(lines) + 1) // 2
        left, right = lines[:half], lines[half:]
        body = ["BT /F1 10 Tf"]
        body.append("1 0 0 1 56 700 Tm")
        for line in left:
            body.append(f"({escape_pdf_text(line)}) Tj 0 -12 Td")
        body.append("1 0 0 1 320 700 Tm")
        for line in right:
            body.append(f"({escape_pdf_text(line)}) Tj 0 -12 Td")
        body.append("ET")
        stream = "\n".join(body).encode("latin-1", "replace")
        content_id = 5 + 2 * index
        objects[4 + 2 * index] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects[content_id] = (
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream
            + b"\nendstream"
        )
    return _assemble(objects, len(topics))


def build_wide_table(pages: int = 4) -> bytes:
    """A page dominated by a space-padded table.

    Tables are where naive extraction is worst: the result is a row of numbers with no punctuation,
    so a claim drawn from one can be supported by a row about a completely different quantity.
    """
    rows = [
        "Band        Target        Measured     Residual    Status",
        "-----       ------        --------     --------    ------",
        "alpha       1.00          1.004        +0.004      pass",
        "beta        2.50          2.487        -0.013      pass",
        "gamma       0.75          0.751        +0.001      pass",
        "delta       3.20          3.196        -0.004      pass",
        "epsilon     1.80          1.802        +0.002      pass",
    ]
    page_one = [
        "7.1 Detector Response by Band",
        "The table below lists the calibrated response of each band.",
        *rows,
        "Every band passed. The largest residual was observed in the beta band.",
    ]
    return build_pdf(["\n".join(page_one)] + ["\n".join(p) for p in _content(pages=pages)[1:]])


def build_long_page(pages: int = 4) -> bytes:
    """One page with far more text than any normal page, to exercise chunk boundaries.

    `pages` defaults to 4 so this layout carries the *same* page-for-page content as every other
    one. That is what makes it comparable: a difference in retrieval between layouts is then a
    difference in layout, not in subject matter.
    """
    sentences = [
        f"Sample {i} was acquired at ninety second intervals and averaged over the window."
        for i in range(140)
    ]
    long_body = ["8.1 Long Acquisition Log", *sentences]
    rest = _content(pages=pages)[1:]
    return build_pdf(["\n".join(long_body)] + ["\n".join(p) for p in rest])


def build_hyphenated(pages: int = 4) -> bytes:
    """Words broken across a line break with a trailing hyphen."""
    hyphenated = [
        "9.1 Signal Chain",
        "The signal chain consists of a colli-mated source, a dichro-ic beam splitter and a",
        "mono-chromator feeding a cooled detec-tor. Each stage is described in turn below.",
        "The colli-mated source reduces the beam divergence before the first optic.",
        "Beam splitting is performed by a dichro-ic element at forty-five degrees.",
    ]
    return build_pdf(["\n".join(hyphenated)] + ["\n".join(p) for p in _content(pages=pages)[1:]])


def build_unicode(pages: int = 4) -> bytes:
    """Non-ASCII content: an em dash, an accented word, a curly quote.

    A PDF with a Type1 base-14 font and WinAnsi encoding can represent these, and a system that
    loses them still returns text \u2014 just quietly wrong text. That is the failure this covers.
    """
    unicode_page = [
        "10.1 Measurement Uncertainty",
        "The uncertainty budget \u2014 including drift, noise and calibration \u2014 totals 0.4 %.",
        "A na\u00efve estimate would omit the drift term entirely.",
        "The report quotes \u201cthe measured value\u201d wherever a figure is reproduced.",
        "E\u00e9lan vital and caf\u00e9 are included to prove non-ASCII survives extraction.",
    ]
    return build_pdf(["\n".join(unicode_page)] + ["\n".join(p) for p in _content(pages=pages)[1:]])


def build_headers_footers(pages: int = 4) -> bytes:
    """A running head and a page number on every page.

    If the running head carried the document title, every retrieved chunk would contain the title,
    and any question naming the title would match every passage in the corpus.
    """
    out = []
    for index, page in enumerate(_content(pages=pages), start=1):
        out.append(
            "\n".join(
                [
                    "Instrument Calibration Report \u2014 Confidential Draft",
                    f"Page {index} of {len(_content(pages=pages))}",
                    "",
                    *page,
                ]
            )
        )
    return build_pdf(out)


def build_scanned(pages: int = 2) -> bytes:
    """Graphics only, no text layer \u2014 exactly what a scanner produces."""
    return build_pdf([""] * pages, graphics_only=True)


def build_encrypted(pages: int = 2) -> bytes:
    return encrypt_pdf(build_pdf(["\n".join(p) for p in _content(pages=pages)][:pages]))


def _assemble(objects: dict[int, bytes], page_count: int) -> bytes:
    """Serialise a hand-built object table into a valid PDF."""
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: dict[int, int] = {}
    for number in sorted(objects):
        offsets[number] = len(out)
        out += f"{number} 0 obj\n".encode("ascii") + objects[number] + b"\nendstream\nendobj\n"
    xref_at = len(out)
    size = max(objects) + 1
    out += f"xref\n0 {size}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for number in range(1, size):
        out += f"{offsets[number]:010d} 00000 n \n".encode("ascii")
    out += (
        f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
    ).encode("ascii")
    return bytes(out)


BUILDERS = {
    "single_column": build_single_column,
    "two_column": build_two_column,
    "wide_table": build_wide_table,
    "long_page": build_long_page,
    "hyphenated": build_hyphenated,
    "unicode": build_unicode,
    "headers_footers": build_headers_footers,
    "scanned": build_scanned,
    "encrypted": build_encrypted,
}


def main() -> int:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    committed = None
    for name, builder in BUILDERS.items():
        payload = builder()
        target = FIXTURE_DIR / f"{name}.pdf"
        target.write_bytes(payload)
        print(f"  {name:<16} {len(payload):>7,} bytes  {target.relative_to(PROJECT_ROOT)}")
        if name == COMMITTED:
            committed = target
    assert committed is not None, "the committed fixture was not built"
    print(f"\ncommitted fixture: {committed.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())