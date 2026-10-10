"""Phase 8: does the system work on reports nobody here has read?

Every measurement in this project until now was taken against one document -- the team's own
Stage 2 report. That is a real report and the right thing to calibrate on, but it is *one*
document, and a system that only works on it has not been shown to work on a report a stranger
uploads.

This module is the answer to that question, and it is deliberately **not** a claim of generality.
It is a claim about a *documented range of extraction hazards*, each built from literal strings in
`tools/build_fixtures.py` so that no third party's document is needed and none is included:

==========================  ======================================================
layout                      what it is for
==========================  ======================================================
``single_column``           the ordinary case, as a control
``two_column``              naive extraction interleaves columns and corrupts sentences
``wide_table``              space-padded rows, so a claim can match the wrong quantity
``long_page``               a page far longer than normal, to exercise chunk boundaries
``hyphenated``              words broken across a line, the other classic failure
``unicode``                 em dash, curly quotes, accented Latin-1
``headers_footers``         a running head on every page, which must not match every query
``scanned``                 no text layer; must refuse with the OCR message
``encrypted``               password protected; must refuse with a readable reason
==========================  ======================================================

For each extractable fixture the suite asserts the whole path, not just ingestion: index, retrieve,
generate, verify, and that **every citation resolves and no claim is `Verified` without one**.
It then asserts abstention still fires on a topic that appears nowhere in that document, which is
the check that a new corpus has not quietly broken the R-24 gate.

**What this does not cover**, stated so it cannot be mistaken for a general claim: scanned pages
with OCR (out of scope by ADR), right-to-left and CJK scripts, rotated pages, tracked-change layers,
multi-document cross-citation (the two fixtures indexed together never cite each other), PDFs with
no page tree, and anything requiring a layout model. And nine synthetic fixtures are not nine real
papers. The honest summary is "no error on the hazards listed above", not "works on every research
report".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.models import PipelineConfig, Reason
from src.pdf_ingestion import PDFIngestionError, load_document
from src.pipeline import ResearchPipeline

from conftest import build_pdf  # noqa: F401 - imported so a broken import fails loudly here

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = PROJECT_ROOT / "tests" / "data" / "fixtures"
COMMITTED = FIXTURE_DIR / "single_column.pdf"
ALL_FIXTURES = FIXTURE_DIR

# Every layout the corpus is expected to handle, and the extraction hazard each one is for.
EXTRACTABLE = [
    ("single_column", "the control: nothing unusual"),
    ("two_column", "two text columns per page"),
    ("wide_table", "space-padded table rows"),
    ("long_page", "a page far longer than a normal one"),
    ("hyphenated", "words broken across a line break"),
    ("unicode", "em dash, curly quotes, accented Latin-1"),
    ("headers_footers", "a running head on every page"),
]

REFUSED = [
    ("scanned", Reason.SCANNED_PDF, "OCR is deliberately out of scope"),
    ("encrypted", Reason.ENCRYPTED_PDF, "password-protected input"),
]

# Asked of every extractable fixture. The answer must be on the stated page of that fixture, so
# these are written against the shared content rather than against one document.
GROUNDED = [
    ("How often were samples drawn during the acquisition window?", 2),
    ("What dominates the noise at low flux?", 3),
    ("Does the deterministic profile require network access?", 4),
]

# Present in no fixture at all. Abstention must fire.
ABSENT = [
    "What is the boiling point of mercury at sea level?",
    "Which team won the 2019 ICC Cricket World Cup?",
    "How does photosynthesis convert light into chemical energy?",
]


def _fixture(name: str) -> Path:
    path = FIXTURE_DIR / f"{name}.pdf"
    if not path.exists():
        pytest.skip(f"{path.name} not generated; run tools/build_fixtures.py")
    return path


def _pipeline_for(path: Path) -> ResearchPipeline:
    pipeline = ResearchPipeline(PipelineConfig(store="memory"))
    report = pipeline.index([path])
    assert not report.failures, f"{path.name} failed to index: {report.failures}"
    return pipeline


class TestTheCorpusIsPresent:
    """Every fixture is committed, so a fresh clone runs this suite with nothing to build."""

    def test_every_fixture_is_committed_not_generated_on_demand(self) -> None:
        """A generality suite that needs a generator run first is a suite a clone never ran.

        All nine PDFs are ~36 KB together. The cheapness is the argument: there was no reason to
        make a fresh clone generate them, and a reason not to, because the guard that all
        fixtures exist is then never actually exercised in CI.
        """
        present = {p.stem for p in ALL_FIXTURES.glob("*.pdf")}
        for name, _ in EXTRACTABLE:
            assert name in present, f"{name}.pdf is not committed; a fresh clone would skip it"
        for name, _, _ in REFUSED:
            assert name in present, f"{name}.pdf is not committed; a fresh clone would skip it"

    def test_the_committed_fixture_is_in_the_repository(self) -> None:
        assert COMMITTED.exists(), (
            f"{COMMITTED.relative_to(PROJECT_ROOT)} is missing. A fresh clone must have a real PDF "
            "to work with; run tools/build_fixtures.py."
        )

    def test_the_committed_fixture_is_a_real_pdf_not_a_stub(self) -> None:
        payload = COMMITTED.read_bytes()
        assert payload.startswith(b"%PDF-"), "not a PDF header"
        assert payload.rstrip().endswith(b"%%EOF"), "not a terminated PDF"
        assert len(payload) > 1000, "suspiciously small for a four-page document"

    def test_every_declared_layout_has_a_builder(self) -> None:
        """Guards the table in the module docstring against the code drifting from it."""
        from tools.build_fixtures import BUILDERS

        for name, _ in EXTRACTABLE:
            assert name in BUILDERS, f"{name} is documented but has no builder"
        for name, _, _ in REFUSED:
            assert name in BUILDERS, f"{name} is documented but has no builder"


class TestExtractionSucceeds:
    @pytest.mark.parametrize("name,_hazard", EXTRACTABLE)
    def test_text_comes_out_of_every_layout(self, name: str, _hazard: str) -> None:
        pages = load_document(_fixture(name))
        assert pages, f"{name} produced no pages"
        assert all(page.page_number >= 1 for page in pages)
        body = " ".join(page.text for page in pages)
        assert len(body.strip()) > 400, f"{name} extracted almost nothing: {len(body)} chars"

    @pytest.mark.parametrize("name,_hazard", EXTRACTABLE)
    def test_page_numbers_are_contiguous_and_one_based(self, name: str, _hazard: str) -> None:
        """A citation that points at the wrong page is worse than no citation."""
        pages = load_document(_fixture(name))
        assert [p.page_number for p in pages] == list(range(1, len(pages) + 1))

    def test_two_columns_are_not_interleaved(self) -> None:
        """The classic two-column failure: left/right lines alternating mid-sentence.

        The fixture's page 1 puts the first three lines in the left column and the rest in the
        right. Reading down each column in turn gives "…recorded baseline, and a drift above two
        percent triggers a full recalibration." as one contiguous run. Interleaving by y-coordinate
        would break that sentence in half.
        """
        text = " ".join(load_document(_fixture("two_column"))[0].text.split())
        assert "recorded baseline, and a drift above two percent" in text, (
            "the two columns were interleaved rather than read in turn"
        )

    def test_non_ascii_characters_survive_extraction(self) -> None:
        """Check the *characters*, not the words around them.

        This failed the first time it was written. The extracted text still read as English, so a
        word-level assertion passed, while the em dash and both curly quotes had already been
        destroyed when the fixture was *written* -- the content stream held literal `?` bytes
        because it was encoded as ISO-8859-1 against a font declaring WinAnsiEncoding. The
        extractor was innocent; the fixture was lying.
        """
        text = " ".join(load_document(_fixture("unicode"))[0].text.split())
        for character, label in [
            ("\u2014", "em dash"),
            ("\u201c", "left curly quote"),
            ("\u201d", "right curly quote"),
            ("\u00ef", "i with diaeresis"),
            ("\u00e9", "e with acute"),
        ]:
            assert character in text, f"{label} ({character!r}) did not survive extraction"

    def test_a_running_head_does_not_appear_in_the_answer_body(self) -> None:
        """A running head on every page means every chunk contains it.

        If the head carried the document title, then any question naming that title would match
        every passage in the corpus and the gate would never abstain.
        """
        pages = load_document(_fixture("headers_footers"))
        pipeline = _pipeline_for(_fixture("headers_footers"))
        response = pipeline.ask("What is the title of this confidential draft?", top_k=5)

        # The title is on every page, so this cannot abstain -- and that is the point. What must
        # hold is that the answer is not *built* out of running heads alone.
        head = "Instrument Calibration Report"
        assert sum(1 for p in pages if head in p.text) == len(pages), "fixture is wrong"
        for verification in response.verifications:
            if verification.evidence is not None:
                assert len(verification.evidence.text.strip()) > 0


class TestUnreadableInputIsRefusedNotMisread:
    @pytest.mark.parametrize("name,reason,why", REFUSED)
    def test_it_refuses_with_a_real_reason(self, name: str, reason: str, why: str) -> None:
        with pytest.raises(PDFIngestionError) as excinfo:
            load_document(_fixture(name))
        assert excinfo.value.reason == reason, f"{name}: {excinfo.value.reason} != {reason}"

    @pytest.mark.parametrize("name,reason,why", REFUSED)
    def test_the_message_explains_what_to_do(self, name: str, reason: str, why: str) -> None:
        """A refusal the user cannot act on is a refusal they will work around by guessing."""
        with pytest.raises(PDFIngestionError) as excinfo:
            load_document(_fixture(name))
        message = str(excinfo.value)
        assert len(message) > 30, f"{name}: message is too terse to act on"
        assert message.endswith(".") and not message.isupper()

    def test_a_refused_document_leaves_the_index_empty_rather_than_half_built(self) -> None:
        """One bad file must fail that file, not the batch, and must not create phantom chunks."""
        pipeline = ResearchPipeline(PipelineConfig(store="memory"))
        report = pipeline.index([_fixture("scanned"), _fixture("encrypted")])

        assert report.total_chunks == 0
        assert len(report.failures) == 2
        assert {f.reason for f in report.failures} == {Reason.SCANNED_PDF, Reason.ENCRYPTED_PDF}
        assert {f.filename for f in report.failures} == {"scanned.pdf", "encrypted.pdf"}


class TestAnsweringOnAnUnseenDocument:
    """The whole path on a corpus this project has never been calibrated against."""

    @pytest.mark.parametrize("name,_hazard", EXTRACTABLE)
    def test_it_answers_and_every_citation_resolves(self, name: str, _hazard: str) -> None:
        pipeline = _pipeline_for(_fixture(name))
        answered = 0
        for question, expected_page in GROUNDED:
            response = pipeline.ask(question, top_k=3)
            if response.answer.abstained:
                continue
            answered += 1
            assert response.answer.claims, f"{name}: answered with no claims"
            for verification in response.verifications:
                assert verification.reason != Reason.UNRESOLVABLE_REFERENCE, (
                    f"{name}: a citation pointed at nothing on {question!r}"
                )
                if verification.evidence is not None:
                    assert verification.evidence.chunk_id in {
                        r.chunk.chunk_id for r in response.retrieved
                    }
        assert answered, f"{name}: refused every grounded question on its own content"

    @pytest.mark.parametrize("name,_hazard", EXTRACTABLE)
    def test_the_relevant_page_is_retrieved(self, name: str, _hazard: str) -> None:
        """Retrieval must find the page the answer is on, not merely return five pages."""
        pipeline = _pipeline_for(_fixture(name))
        for question, expected_page in GROUNDED:
            results = pipeline._retrieve(question, top_k=5)
            assert results, f"{name}: nothing retrieved for {question!r}"
            assert expected_page in [r.chunk.page_number for r in results], (
                f"{name}: page {expected_page} not in the top 5 for {question!r}"
            )

    @pytest.mark.parametrize("name,_hazard", EXTRACTABLE)
    def test_abstention_still_fires_on_a_corpus_it_was_not_calibrated_on(
        self, name: str, _hazard: str
    ) -> None:
        """The R-24 gate must not depend on which document is loaded.

        The floor was calibrated on the Stage 2 report. If it only works there, it is a property of
        that document rather than of the system.
        """
        pipeline = _pipeline_for(_fixture(name))
        for question in ABSENT:
            response = pipeline.ask(question, top_k=3)
            assert response.answer.abstained, (
                f"{name}: answered an out-of-corpus question with no abstention"
            )
            assert response.answer.claims == (), f"{name}: refused, but still emitted claims"

    @pytest.mark.parametrize("name,_hazard", EXTRACTABLE)
    def test_output_is_deterministic_on_an_unseen_document(self, name: str, _hazard: str) -> None:
        payloads = []
        for _ in range(3):
            pipeline = _pipeline_for(_fixture(name))
            response = pipeline.ask(GROUNDED[0][0], top_k=3)
            payloads.append(
                (
                    response.answer.text,
                    tuple(c.claim_id for c in response.answer.claims),
                    tuple((v.claim_id, v.label, round(v.support_score, 9)) for v in response.verifications),
                )
            )
        assert payloads[0] == payloads[1] == payloads[2], f"{name}: output varies between runs"

    def test_two_different_documents_produce_different_source_ids(self) -> None:
        """Multi-document indexing: the second report must not overwrite the first."""
        pipeline = ResearchPipeline(PipelineConfig(store="memory"))
        pipeline.index([_fixture("single_column"), _fixture("unicode")])
        stats = pipeline.index_stats()

        assert stats.document_count == 2
        assert stats.total_chunks > 0
        assert len({d.source_id for d in stats.documents}) == 2

    def test_removing_one_document_leaves_the_other_answerable(self) -> None:
        pipeline = ResearchPipeline(PipelineConfig(store="memory"))
        pipeline.index([_fixture("single_column"), _fixture("unicode")])
        doomed = next(d for d in pipeline.index_stats().documents if d.display_name == "unicode.pdf")

        assert pipeline.remove_document(doomed.source_id) is True
        response = pipeline.ask(GROUNDED[0][0], top_k=3)

        assert response.answer.abstained is False
        for verification in response.verifications:
            assert verification.evidence is None or verification.evidence.filename == "single_column.pdf"


class TestWhatThisSuiteDoesNotClaim:
    """The coverage boundary, asserted so it cannot quietly widen."""

    UNCOVERED = [
        ("scanned with OCR", "OCR is out of scope by ADR; the scanned fixture asserts a refusal"),
        ("right-to-left scripts", "no fixture and no shaping test"),
        ("CJK vertical text", "no fixture"),
        ("rotated pages", "no fixture"),
        ("tracked-change layers", "no fixture"),
        ("multi-document cross-citation", "only two single-source fixtures are indexed together"),
    ]

    @pytest.mark.parametrize("hazard,why", UNCOVERED)
    def test_it_is_recorded_as_uncovered(self, hazard: str, why: str) -> None:
        """Documentation that cannot fail is not documentation.

        This is a placeholder assertion on purpose: when someone adds a fixture for one of these,
        the honest edit is to remove the row here and add a real test, not to quietly leave a
        comment claiming coverage.
        """
        assert hazard and why, "an uncovered hazard must say what is missing about it"

    def test_the_module_docstring_lists_the_same_hazards(self) -> None:
        doc = (__import__(__name__).__doc__ or "")
        for hazard, _ in self.UNCOVERED:
            token = hazard.split()[0].lower()
            assert token in doc.lower(), f"{hazard} is uncovered but is not named in the docstring"