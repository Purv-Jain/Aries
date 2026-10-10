"""Capture genuine screenshots of the running application.

Every image this produces comes from a real Streamlit process answering real questions about a real
PDF. Nothing is mocked, no HTML is injected, and no placeholder state is staged. If a panel looks
empty it is empty because the app says it is empty.

**Which document.** The committed synthetic fixture at
`tests/data/fixtures/single_column.pdf`, not the team's Stage 2 report. The report names its authors,
their PRNs and their project guide, and screenshots of its pages committed to a public repository would
publish it \u2014 which is the decision Phase E declined to make. The fixture also means the evidence is
reproducible from a fresh clone by anyone who checks this file.

    .venv\\Scripts\\python.exe -X utf8 tools\\capture_screenshots.py

Requires Playwright and its Chromium build. Both are development-time tooling and neither is a
runtime dependency of the application: the app itself still has no network requirement, no browser
requirement and no paid API.

Images land in `docs/screenshots/` as PNGs at a fixed 1440x900 viewport, named `S1`\u2026`S5` to match
the nine-state list in `docs/11_DEMO_AND_VIVA_PREPARATION.md`. Each is captured only after the state
it shows has been *verified present in the DOM*, so a screenshot can never show a panel that did not
render.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHOTS = PROJECT_ROOT / "docs" / "screenshots"
FIXTURE = PROJECT_ROOT / "tests" / "data" / "fixtures" / "single_column.pdf"

PORT = 8623
VIEWPORT = {"width": 1440, "height": 900}

# A question the fixture answers, and one that appears in no fixture at all.
ANSWERABLE = "How often were samples drawn during the acquisition window?"
OUT_OF_CORPUS = "What is the boiling point of mercury at sea level?"

# A citation button in the answer legend, by grammar rather than by literal.
MARKER_BUTTON = re.compile(r"^S\d+,\s*p\.\d+$")


def _wait_for_server(url: str, timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            time.sleep(2)
    raise SystemExit(f"streamlit did not become ready at {url} within {timeout}s")


def _start_streamlit() -> subprocess.Popen:
    command = [
        sys.executable, "-X", "utf8", "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--server.port", str(PORT),
        "--browser.gatherUsageStats", "false",
    ]
    process = subprocess.Popen(
        command, cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    _wait_for_server(f"http://localhost:{PORT}")
    return process


def _wait_for(page, needle: str, what: str, timeout_ms: int = 90000) -> None:
    """Block until `needle` is on the page.

    Three earlier versions got this wrong, and every failure pointed at the application rather
    than at the check:

    * Polling for the status widget to disappear fails on first load -- the widget does not exist
      yet, so `count() == 0` means "has not started", not "has finished".
    * Polling for a fixed interval and then returning anyway gave up at 16 s while a cold render
      takes about 18 s on this machine.
    * Requiring the status widget to be absent *as well as* the needle present was intermittent:
      it passed four runs and failed the fifth, purely on where Streamlit happened to be in its
      rerun cycle.

    So the condition is now **only** the needle, which is the stronger signal regardless: the text
    appears when that panel has rendered, so there is nothing to wait for afterwards. A short settle
    and a re-check guard against catching it mid-paint.
    """
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if _has(page, needle):
            page.wait_for_timeout(900)  # let the rest of the panel paint
            if _has(page, needle):
                return
        page.wait_for_timeout(300)
    raise SystemExit(
        f"timed out after {timeout_ms} ms waiting for {what}: {needle!r} never appeared. This is a "
        "harness or timing fault, not a claim about the application."
    )
def _has(page, needle: str) -> bool:
    """True when `needle` is on the page, by either measure.

    Two checks, because on this Streamlit build they do not agree:

    * `page.inner_text("body")` returns **rendered** text. It reported the workspace's
      "Ask a question to see an answer..." note, and did *not* report the library's filename.
    * `page.content()` returns serialised **HTML**. It reported the filename, and did *not*
      contain that workspace note.

    So neither alone is reliable, and using only one produced a false "the panel never rendered"
    twice -- once in each direction, both of which pointed at the application when the fault was
    in the check. Accepting either is the fix; the needles are distinctive enough
    ("single_column.pdf", "Ask a question", "S1, p.") that a false positive is not a real risk.
    """
    try:
        if needle in page.inner_text("body"):
            return True
    except Exception:  # noqa: BLE001 - a detached body during navigation is not a failure
        pass
    try:
        return needle in page.content()
    except Exception:  # noqa: BLE001
        return False


def _require(page, needle: str, what: str) -> None:
    """Fail loudly unless `needle` is already on the page.

    The point of this is that a screenshot is *evidence*. Capturing first and hoping is how a
    report ends up showing a panel that never rendered.
    """
    if not _has(page, needle):
        raise SystemExit(f"refusing to capture {what}: {needle!r} is not on the page")


def _shoot(page, name: str, what: str) -> Path:
    SHOTS.mkdir(parents=True, exist_ok=True)
    target = SHOTS / f"{name}.png"
    page.screenshot(path=str(target))
    print(f"  {name}.png  {target.stat().st_size:>8,} bytes  ({what})")
    return target


def main() -> int:
    from playwright.sync_api import sync_playwright

    if not FIXTURE.exists():
        raise SystemExit(f"fixture missing: {FIXTURE}")

    server = _start_streamlit()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
            page.goto(f"http://localhost:{PORT}", wait_until="domcontentloaded")
            _wait_for(page, "Dashboard", "the navigation to render")

            # -- S1: the dashboard in its real, empty, pre-upload state ---------------
            _require(page, "Drop academic PDFs here", "the upload panel")
            _shoot(page, "S1_dashboard_empty", "dashboard before upload: the real empty state")

            # Upload. Streamlit's uploader is a real <input type=file>; setting files on it is
            # what a user's drop actually does, so indexing runs end to end. The proof it worked
            # is the document appearing in the Library, not a sleep.
            page.set_input_files('input[type="file"]', str(FIXTURE))
            # Wait for the upload to actually be *processed* while still on the Dashboard. The
            # filename appears here first, which is the proof the file landed; navigating straight
            # to the Library raced it and showed an empty library -- a harness fault that looks
            # exactly like a broken upload path.
            _wait_for(page, "single_column.pdf", "the upload to be processed")

            # -- S2: the indexed document library --------------------------------------
            page.get_by_text("Library", exact=True).first.click()
            _wait_for(page, "single_column.pdf", "the uploaded document to reach the library")
            _shoot(page, "S2_library_indexed", "indexed document library")

            # -- S3: a grounded answer with citations ----------------------------------
            page.get_by_text("Workspace", exact=True).first.click()
            _wait_for(page, "Ask a question", "the workspace")
            page.get_by_placeholder("What technology stack does the report specify?").fill(ANSWERABLE)
            page.get_by_role("button", name="Ask").click()
            _wait_for(page, "S1, p.", "a grounded answer carrying a citation marker")
            _shoot(page, "S3_answer_with_citations", "grounded answer carrying [Sx, p.y] markers")

            # -- S4: per-claim verification with the cited passage open ------------------
            _require(page, "Claim by claim", "the verification panel")
            # Not hardcoded to "S1, p.1": the marker that carries the top claim depends on which
            # page the answer came from. Matching the grammar finds whichever one is there, which
            # is also what a user clicks.
            page.get_by_role("button", name=MARKER_BUTTON).first.click()
            _wait_for(page, "Support score", "the evidence inspector")
            _shoot(page, "S4_verification_evidence", "per-claim verification and the cited passage")

            # -- S5: an out-of-corpus question, and the refusal -------------------------
            page.get_by_placeholder("What technology stack does the report specify?").fill(OUT_OF_CORPUS)
            page.get_by_role("button", name="Ask").click()
            _wait_for(page, "No answer was produced", "the abstention panel")
            _require(page, "mercury", "the refusal naming the unmatched term")
            _shoot(page, "S5_abstention", "out-of-corpus question refused, naming the unmatched terms")

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:  # pragma: no cover
            server.kill()

    print(f"\n{SHOTS.relative_to(PROJECT_ROOT)} now holds:")
    for image in sorted(SHOTS.glob("*.png")):
        print(f"  {image.name:<28} {image.stat().st_size:>9,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())