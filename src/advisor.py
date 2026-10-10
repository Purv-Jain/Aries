"""Turn a verification result into an action the author can take.

`verifier.py` answers *what did the system find*. This module answers *what should change*, and it
is the last stage that turns the project's output into something a person can act on.

One function, `advise`, maps each `ClaimVerification.reason` to a correction:

| reason | action | what it tells the author |
|---|---|---|
| `no_marker` | `add_citation` | this claim has no citation at all |
| `page_mismatch` | `fix_page_number` | the source exists but at a different page |
| `unresolvable_reference` | `replace_fabricated_citation` | the cited passage was never retrieved |
| `malformed_marker` | `resolve_marker_syntax` | the citation is not in the required format |
| `numeric_mismatch` | `reword_to_match_source` | a number is not in the cited passage |
| `contradiction_detected` | `reword_to_match_source` | the passage asserts the opposite |
| `weak_support` | `none` | thin overlap; not automatically an error |
| `supported` | `none` | nothing to do |

**Why the mapping is conservative in both directions.** `weak_support` produces no correction even
though it is not `Verified`, because low lexical overlap is the *documented* weakness of a
containment-based score on paraphrase (D-26) and not evidence of a mistake. Recommending a change
for a correct paraphrase would train people to ignore the advice, and advice that is routinely wrong
is worse than no advice. `contradiction_detected` is treated as a real finding because it is a
directional check with a named cause, not a similarity threshold.

**Two limits, stated rather than papered over.**

* This cannot tell *whether the source is right*. It only compares a claim with the passage that
  claim cites. If the document itself is wrong, a perfectly supported citation is still wrong, and
  nothing here detects that.
* The `repair_prompt` is a convenience, not an authority. It is built **only from the retrieved
  passage and the claim** -- never from the document as a whole -- so it cannot carry in context the
  user has not already seen. It asks an assistant to help reword, and it explicitly instructs that
  assistant to preserve any number present in the source, because the most damaging "improvement" to
  a citation is a fluent sentence with an invented figure in it.

The module is pure: no I/O, no network, no model, no clock. `Correction` and `CorrectionPlan` come
from `models.py`, and this is the only module that constructs them.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from src.models import (
    ClaimVerification,
    Correction,
    CorrectionPlan,
    Reason,
)

__all__ = ["advise", "REASON_ACTIONS"]


# The mapping above, as data. A test asserts it covers every `Reason` the verifier can emit, so a
# new reason code cannot be added without deciding what advice it produces.
REASON_ACTIONS: Mapping[str, str] = {
    Reason.NO_MARKER: "add_citation",
    Reason.PAGE_MISMATCH: "fix_page_number",
    Reason.UNRESOLVABLE_REFERENCE: "replace_fabricated_citation",
    Reason.MALFORMED_MARKER: "resolve_marker_syntax",
    Reason.NUMERIC_MISMATCH: "reword_to_match_source",
    Reason.CONTRADICTION_DETECTED: "reword_to_match_source",
    # No shared vocabulary at all is not a wording problem. Rewording will not make a claim about a
    # different subject match a passage about this one, so the honest advice is to remove the claim
    # or cite the passage that actually supports it.
    Reason.NO_SUPPORT: "remove_unsupported_claim",
    Reason.WEAK_SUPPORT: "none",
    Reason.SUPPORTED: "none",
}


def _suggestion(verification: ClaimVerification, action: str) -> str:
    """One specific, actionable sentence. Never "consider revising"."""
    evidence = verification.evidence
    page = evidence.page_number if evidence else None
    filename = evidence.filename if evidence else "the cited document"

    if action == "add_citation":
        return (
            "This claim states something checkable but cites nothing, so a reader cannot trace it. "
            "Add a citation of the form [S1, p.N] pointing at the passage that states it, or remove "
            "the claim if the document does not actually make it."
        )
    if action == "fix_page_number":
        return (
            "The cited source was retrieved, but at a different page than the one named. Correct the "
            "page number to the page that actually contains the passage. This system will not "
            "re-point the citation for you, because silently moving a citation is exactly the "
            "failure it exists to prevent."
        )
    if action == "replace_fabricated_citation":
        return (
            "The answer cites a source that was not among the passages retrieved for this question, "
            "so the citation cannot be checked. Replace it with a citation to a passage that was "
            "actually retrieved, or drop the claim."
        )
    if action == "resolve_marker_syntax":
        return (
            "The citation could not be parsed. The required form is [S1, p.5] for one passage, or "
            "[S1, p.5; S2, p.9] for several. A malformed marker is reported rather than guessed at, "
            "so it cannot be repaired automatically."
        )
    if action == "reword_to_match_source":
        if verification.reason == Reason.NUMERIC_MISMATCH:
            return (
                "A number in this claim does not appear in the passage it cites. Either the number "
                "is wrong, or the citation points at the wrong passage. A number cannot be "
                "supported by a passage that does not contain it, so this one has to be fixed "
                "rather than reworded."
            )
        if verification.reason == Reason.CONTRADICTION_DETECTED:
            return (
                "The cited passage appears to assert the opposite of this claim. Read the passage: "
                "either the claim inverts the source, or the source does not say what the claim "
                "says it says."
            )
        return (
            "The claim and the passage it cites share too little wording for this system to treat "
            "them as the same statement. Reword the claim closer to the passage's own phrasing, or "
            "if the two genuinely say different things, cite the passage that matches."
        )
    if action == "remove_unsupported_claim":
        return (
            "Nothing in the cited passage supports this claim. Remove it, or cite the passage that "
            "does support it."
        )
    return "No correction needed."


def _repair_prompt(verification: ClaimVerification, action: str) -> str:
    """A pasteable prompt for a general-purpose assistant.

    Built only from the claim and the retrieved passage. The instruction to preserve numbers is
    load-bearing: a plausible rewrite that changes "180 words" to "200 words" is a *worse* defect
    than the one being fixed, and this is the step most likely to introduce it.
    """
    evidence = verification.evidence
    passage = evidence.text.strip() if evidence else ""
    page = evidence.page_number if evidence else None
    where = f"page {page}" if page else "the cited passage"

    return (
        "I am checking citations in an academic document and need help rewriting one sentence so "
        "that it matches its source.\n\n"
        f"CLAIM: \"{verification.claim_text}\"\n\n"
        f"SOURCE PASSAGE ({where}):\n\"{passage}\"\n\n"
        f"PROBLEM: {verification.explanation}\n\n"
        "Rewrite the claim so that it is fully supported by the source passage above. Rules: use "
        "only information present in the passage; keep every number, date, unit and proper noun "
        "exactly as the passage states them -- never introduce a figure that is not there; keep the "
        "original citation marker unchanged; do not add information from your own knowledge. "
        "Return the rewritten claim on one line, then a one-sentence note explaining what you "
        "changed and why."
        if action != "add_citation"
        else (
            "I am checking citations in an academic document and one claim has no citation at all.\n\n"
            f"CLAIM: \"{verification.claim_text}\"\n\n"
            "Rewrite this claim so that it is clearly checkable against a specific source, and tell "
            "me what kind of evidence would be needed to support it. Use only what is in the claim "
            "itself -- do not invent a source, a figure or a citation. If the claim cannot be "
            "supported without adding new information, say so plainly instead of inventing one."
        )
    )


def _single(verification: ClaimVerification) -> Correction:
    action = REASON_ACTIONS.get(verification.reason, "none")
    return Correction(
        claim_id=verification.claim_id,
        claim_text=verification.claim_text,
        action=action,
        suggestion=_suggestion(verification, action),
        repair_prompt=_repair_prompt(verification, action),
        evidence_page=verification.evidence.page_number if verification.evidence else None,
        current_marker=None,
    )


def _summary_prompt(corrections: Sequence[Correction], headline: str) -> str:
    """One prompt covering every finding, for the author who wants a single pass."""
    if not corrections:
        return (
            "No citation problems were detected in this answer. Nothing to repair."
        )
    blocks = []
    for index, correction in enumerate(corrections, start=1):
        blocks.append(
            f"{index}. CLAIM: \"{correction.claim_text}\"\n"
            f"   PROBLEM: {correction.suggestion}"
        )
    return (
        "I am checking citations in an academic document. The following claims were flagged by an "
        "automated citation checker. For each one, suggest a rewrite that would be fully supported "
        f"by its cited source.\n\n{headline}\n\n"
        + "\n".join(blocks)
        + "\n\nRules for every rewrite: use only information from the cited passage; keep every "
        "number, date, unit and proper noun exactly as the source states it; never introduce a "
        "figure that is not present in the source; do not use outside knowledge; keep the original "
        "citation markers unchanged. Return the rewrites as a numbered list, and say 'no change "
        "needed' for any claim that is already correctly cited."
    )


def advise(
    verifications: Sequence[ClaimVerification],
    *,
    headline: str = "",
) -> CorrectionPlan:
    """Turn verified results into corrections, most-actionable first.

    Deterministic and pure. Ordering is by action severity, then by the order claims appeared in the
    answer, so the same answer always produces the same plan -- which is what lets a test assert on
    it and lets a reader find the same item in the same place.

    An abstained answer yields an empty plan rather than a plan saying "no corrections found",
    because those are different facts: the first means the system checked and found nothing wrong,
    the second means it never checked.
    """
    if not verifications:
        return CorrectionPlan(corrections=(), summary_prompt="")

    # Keyed by *action*, not by reason. The first version keyed this by reason and put
    # `page_mismatch` first, which silently demoted `fix_page_number` below every `none` entry --
    # a wrong page being the most likely to be missed and the most mechanical to fix.
    severity = {
        "replace_fabricated_citation": 0,
        "fix_page_number": 1,
        "resolve_marker_syntax": 2,
        "reword_to_match_source": 3,
        "remove_unsupported_claim": 4,
        "add_citation": 5,
        "none": 6,
    }
    corrections = [_single(verification) for verification in verifications]
    corrections.sort(key=lambda item: (severity.get(item.action, 9), item.claim_id))

    actionable = [c for c in corrections if c.action != "none"]
    if not actionable:
        return CorrectionPlan(
            corrections=(),
            summary_prompt=_summary_prompt(
                (), headline or "Every claim resolved to a retrieved passage and was supported."
            ),
        )
    return CorrectionPlan(
        corrections=tuple(corrections),
        summary_prompt=_summary_prompt(actionable, headline),
    )