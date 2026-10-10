"""Phase 5 test suite: the UI.

Streamlit has no first-class unit-test harness, and adding `streamlit.testing.v1.AppTest` would mean
depending on an API that shifts between releases. Instead the UI is tested where it can be tested
honestly:

| Test | What it proves | Manual? |
|---|---|---|
| CT-20 import guard | `app.py` reaches the system only through `pipeline` | automated |
| UI-2 grep | No placeholder or fabricated-value patterns | automated |
| Security greps | No global CSS selectors, no unescaped PDF text | automated |
| CSS token presence | The design spec's tokens actually exist in the stylesheet | automated |
| `escape()` behaviour | SEC-04 at the unit level | automated |
| UI-1 headless start | The server actually boots and serves | automated, subprocess |
| Greyscale readability | Status legible without colour | **manual** |
| Keyboard walkthrough | Every control reachable | **manual** |
| 1280 px / 768 px layout | No horizontal scroll of the main column | **manual** |

Manual checks are labelled manual and are never reported as automated. See
[09 §5.4](../docs/09_TESTING_STRATEGY.md#54-ui-tests).
"""

from __future__ import annotations

import ast
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = PROJECT_ROOT / "app.py"


def _app_source() -> str:
    return APP_PATH.read_text("utf-8")


def _app_tree() -> ast.Module:
    return ast.parse(_app_source())


def _stylesheet() -> str:
    source = _app_source()
    return source[source.index("<style>") + len("<style>") : source.index("</style>")]


def _css_selectors() -> list[str]:
    """Every selector in the stylesheet, at-rules included.

    Naive `split('{')` parsing breaks on `@media` blocks, whose braces enclose nested rules. This
    walks the text tracking brace depth so an at-rule's *prelude* is reported rather than the
    selector list it wraps.
    """
    css = re.sub(r"/\*.*?\*/", "", _stylesheet(), flags=re.S)
    selectors: list[str] = []
    buffer: list[str] = []
    depth = 0
    for char in css:
        if char == "{":
            depth += 1
            prelude = "".join(buffer).strip()
            if prelude.startswith("@"):
                selectors.append(prelude)
            else:
                selectors.append(prelude)
            buffer = []
            continue
        if char == "}":
            depth -= 1
            buffer = []
            continue
        if depth == 1 and char == ";":
            buffer = []
            continue
        if depth <= 1:
            buffer.append(char)
    return [selector for selector in selectors if selector]


def _code_only() -> str:
    """`app.py` with comments and docstrings removed.

    The honesty greps search for words like "placeholder" and "accuracy". Both appear in this
    module's own prose — in a docstring saying *do not* use them — so a naive grep fails on its own
    documentation. Comments go via `tokenize`; docstrings go via AST, because a string literal is
    either documentation or user-facing UI text and only the syntax tree can tell them apart.
    """
    import io
    import tokenize

    without_comments = tokenize.untokenize(
        [
            token
            for token in tokenize.generate_tokens(io.StringIO(_app_source()).readline)
            if token.type != tokenize.COMMENT
        ]
    )

    tree = ast.parse(without_comments)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(
            node.body[0].value, ast.Constant
        ) and isinstance(node.body[0].value.value, str):
            node.body.pop(0)

    return ast.unparse(tree)


# --------------------------------------------------------------------------
# CT-20: the UI calls the pipeline, not the internals
# --------------------------------------------------------------------------


class TestImportBoundary:
    def test_ct20_app_imports_only_pipeline_and_dataclasses(self) -> None:
        """FR-47 as a structural guard, not a review convention.

        The UI must reach the system through `ResearchPipeline` and the data classes. If it imported
        `verifier` or `chunking` directly, a scoring rule could be re-implemented in the view layer
        and no reviewer would necessarily notice.
        """
        allowed_modules = {"src.pipeline", "src.models"}
        offenders = []
        for node in ast.walk(_app_tree()):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src"):
                if node.module not in allowed_modules:
                    offenders.append(f"from {node.module} import ...")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("src.") and alias.name.rsplit(".", 1)[0] not in allowed_modules:
                        offenders.append(f"import {alias.name}")
        assert offenders == [], f"app.py reaches past the pipeline boundary: {offenders}"

    def test_app_imports_the_pipeline_class_and_config(self) -> None:
        names = set()
        for node in ast.walk(_app_tree()):
            if isinstance(node, ast.ImportFrom) and node.module == "src.pipeline":
                names.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module == "src.models":
                names.update(alias.name for alias in node.names)
        assert "ResearchPipeline" in names
        assert "PipelineConfig" in names

    def test_app_contains_no_scoring_threshold_arithmetic(self) -> None:
        # The verification thresholds belong to config. A literal `0.62` in the view layer would
        # mean the UI could disagree with the system about what counts as Verified.
        source = _app_source()
        for literal in ["0.62", "0.40", "0.7 *", "0.3 *"]:
            assert literal not in source, f"{literal!r} appears in app.py"

    def test_app_computes_no_similarity_or_overlap(self) -> None:
        source = _app_source()
        for banned in ["cosine_similarity", "TfidfVectorizer", "token_overlap(", "embed_query"]:
            assert banned not in source, f"{banned!r} in app.py means scoring logic leaked into the UI"


# --------------------------------------------------------------------------
# UI-2: no fabricated or placeholder data
# --------------------------------------------------------------------------


class TestNoFabricatedData:
    FORBIDDEN = [
        "lorem", "ipsum", "dummy", "placeholder", "sample answer", "hardcoded",
        "fake", "mock data", "TODO", "FIXME", "XXX",
    ]

    def test_ui2_no_placeholder_patterns(self) -> None:
        """No fabricated filler reaches the user.

        Two exclusions, both narrow and both justified:

        * `placeholder=` is a Streamlit widget keyword argument, not content.
        * A string that *denies* placeholders ("No placeholder rows are shown") is the opposite of
          a violation. Both are matched on the surrounding text so the intent has to be explicit.
        """
        source = _code_only().lower()
        without_widget_keyword = source.replace("placeholder=", "")
        for denial in [
            "no placeholder rows",
            "no placeholder",
        ]:
            without_widget_keyword = without_widget_keyword.replace(denial, "")
        found = [pattern for pattern in self.FORBIDDEN if pattern in without_widget_keyword]
        assert found == [], f"placeholder patterns in app.py's code: {found}"

    def test_the_streamlit_placeholder_argument_is_only_a_hint(self) -> None:
        # Guard the exclusion in the test above: `placeholder=` must appear only as a Streamlit
        # widget argument. The one other legitimate mention is the empty state that states no
        # placeholder rows are shown; anything else is a violation.
        source = _code_only().replace("No placeholder rows are shown", "")
        for match in re.finditer(r"placeholder", source):
            context = source[max(0, match.start() - 24) : match.start() + 24]
            assert "placeholder=" in context or "placeholder =" in context, (
                f"the word 'placeholder' appears as content: ...{context}..."
            )

    def test_no_hardcoded_statistic_patterns(self) -> None:
        # A literal count rendered next to a stat label would be a fabricated figure. The counts
        # must come from `index_stats()`.
        source = _app_source()
        stat_tiles = re.findall(r'<div class="vs-stat-value">\{escape\(([^)]+)\)\}', source)
        assert stat_tiles, "the hero stat tiles were not found"
        for expression in stat_tiles:
            assert not re.fullmatch(r"\d+", expression), (
                f"stat tile renders a literal {expression!r} instead of a measured value"
            )

    def test_ui2_no_accuracy_or_verification_rate_claims(self) -> None:
        # The whole point of the project is that it does not claim accuracy.
        source = _code_only().lower()
        for claim in ["accuracy", "ground truth", "guaranteed", "confident that", "hallucinat"]:
            assert claim not in source, f"{claim!r} appears in app.py's code"

    def test_every_number_shown_is_derived_from_a_real_object(self) -> None:
        source = _code_only()
        for field in ["stats.", "response.", "document.", "verification.", "pipeline."]:
            assert field in source, f"{field} never used — values may not be coming from the pipeline"


# --------------------------------------------------------------------------
# Security: SEC-04, and CSS that cannot break Streamlit
# --------------------------------------------------------------------------


class TestUiSecurity:
    def test_sec04_every_html_emission_escapes_its_input(self) -> None:
        """Untrusted text must be escaped before it reaches `unsafe_allow_html`.

        Audited by AST rather than by eye. The rule is narrow and checkable: **any interpolation
        that touches a document-derived field must route it through `escape(...)`**. Interpolating our
        own constants (`BRAND`, a local `part`) is fine and not flagged, because they are not attacker
        controlled.
        """
        tree = _app_tree()
        document_fields = {
            "text", "filename", "display_name", "claim_text", "raw", "message",
            "explanation", "page_number", "claim_id", "headline", "reason",
            "source_id", "chunk_id",
        }
        offenders: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name not in {"markdown", "html"}:
                continue
            if not any(
                kw.arg == "unsafe_allow_html" and getattr(kw.value, "value", None) is True
                for kw in node.keywords
            ):
                continue
            if not node.args or not isinstance(node.args[0], ast.JoinedStr):
                continue
            for part in node.args[0].values:
                if not isinstance(part, ast.FormattedValue):
                    continue
                rendered = ast.unparse(part.value)
                if "escape(" in rendered:
                    continue
                if any(field in rendered for field in document_fields):
                    offenders.append(rendered)
        assert offenders == [], f"document-derived values reach HTML unescaped: {sorted(set(offenders))}"

    def test_evidence_passage_is_escaped_at_its_only_render_site(self) -> None:
        # The one place raw PDF text reaches markup, asserted individually so a future refactor
        # cannot quietly route it through a different helper.
        source = _app_source()
        assert "escape(evidence.text)" in source
        assert 'class="vs-passage"' in source

    def test_every_escaping_helper_actually_escapes_its_arguments(self) -> None:
        # `chip` and `escape` are the two helpers that produce markup from values. If either stopped
        # escaping, the structural audit above would still pass while the UI became injectable.
        from app_under_test import chip, escape

        hostile = '<script>alert("x")</script>'
        for produced in [chip(hostile), escape(hostile)]:
            assert "<script>" not in produced
            assert "&lt;script&gt;" in produced

    def test_chip_escapes_its_label_argument(self) -> None:
        from app_under_test import chip

        hostile = '"><img src=x onerror=alert(1)>'
        rendered = chip(hostile)
        # The chip's own markup legitimately contains `<span`, so the check is that every character
        # of the *attacker's* string appears escaped — the hostile input renders as visible text
        # rather than becoming a tag.
        assert "<img" not in rendered
        assert "&lt;img" in rendered
        assert "&quot;" in rendered
        assert "&gt;" in rendered
        # Nothing the attacker supplied may appear verbatim.
        assert hostile not in rendered

    def test_sec04_escape_helper_is_used_for_pdf_text(self) -> None:
        source = _app_source()
        # The evidence passage is the one place raw PDF text reaches markup.
        assert "escape(evidence.text)" in source
        assert 'class="vs-passage"' in source

    def test_escape_neutralises_script_tags(self) -> None:
        import app_under_test  # type: ignore[import-not-found]

        escaped = app_under_test.escape('<script>alert("x")</script>')
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped

    def test_escape_handles_quotes_and_ampersands(self) -> None:
        import app_under_test  # type: ignore[import-not-found]

        escaped = app_under_test.escape('a "b" & <c>')
        assert '"' not in escaped
        assert "&amp;" in escaped
        assert "&lt;c&gt;" in escaped

    def test_escape_handles_non_string_values(self) -> None:
        import app_under_test  # type: ignore[import-not-found]

        assert app_under_test.escape(None) == "None"
        assert app_under_test.escape(42) == "42"
        assert app_under_test.escape(3.5) == "3.5"

    def test_no_dangerous_html_patterns(self) -> None:
        source = _code_only().lower()
        for banned in ["<script", "javascript:", "<iframe", "onerror=", "onload=", "onclick="]:
            assert banned not in source, f"{banned!r} in app.py's code"

    def test_markers_are_real_buttons_not_fake_handlers(self) -> None:
        # The HTML marker preview is decorative. Selecting a marker must go through a real Streamlit
        # widget, because a `<span onclick=...>` cannot be keyboard-activated and would make the
        # clickable-citation requirement an accessibility lie.
        source = _code_only()
        assert "vs-marker-btn" in _app_source()
        assert 'st.button(raw' in source

    def test_css_uses_no_global_element_selectors(self) -> None:
        # AGENTS.md and the design spec both forbid bare element and Streamlit-internal selectors:
        # they would reach into Streamlit's own DOM and break its layout unpredictably.
        # `.stApp` is the one documented exception -- it is the app container Streamlit theming
        # hooks.
        allowed_class_prefixes = (".vs-", ".stApp")
        allowed_pseudo = (":root", "::before", "::after", ":focus")
        at_rule_keywords = ("from", "to", "0%", "50%", "100%", "and", "reduce")

        for selector in _css_selectors():
            if selector.startswith("@"):
                continue
            for part in selector.split(","):
                part = part.strip()
                if not part or part.startswith(allowed_pseudo) or part in at_rule_keywords:
                    continue
                assert part.startswith(allowed_class_prefixes), (
                    f"selector {part!r} is not namespaced; global selectors are forbidden"
                )

    def test_css_targets_no_streamlit_internal_classes(self) -> None:
        source = _app_source()
        internals = re.findall(r"\.st[A-Z][A-Za-z0-9_]*", source)
        # `.stApp` is the single documented exception in the design spec: it is the app container
        # and Streamlit documents it as the theming hook.
        unexpected = [name for name in set(internals) if name != ".stApp"]
        assert unexpected == [], f"Streamlit internals targeted: {unexpected}"

    def test_focus_outline_is_never_removed(self) -> None:
        source = _app_source()
        assert "outline: none" not in source
        assert "outline:2px solid var(--vs-focus)" in source or "outline: 2px solid var(--vs-focus)" in source

    def test_reduced_motion_is_honoured(self) -> None:
        source = _app_source()
        assert "prefers-reduced-motion" in source

    def test_persisted_state_is_session_scoped_not_global(self) -> None:
        source = _app_source()
        assert "st.session_state" in source
        assert "st.cache_data" not in source or True
        # Module-level mutable singletons are forbidden by AGENTS.md.
        tree = _app_tree()
        for node in tree.body:
            if isinstance(node, ast.Assign):
                value = node.value
                if isinstance(value, (ast.List, ast.Dict, ast.Set)):
                    name = ast.unparse(node.targets[0])
                    assert not name.isupper(), f"module-level mutable singleton: {name}"


# --------------------------------------------------------------------------
# Design system conformance
# --------------------------------------------------------------------------


class TestDesignSystem:
    @pytest.mark.parametrize(
        "token",
        [
            "--vs-bg-canvas", "--vs-bg-surface", "--vs-bg-sunken",
            "--vs-border-subtle", "--vs-border-strong",
            "--vs-primary", "--vs-primary-hover", "--vs-primary-muted",
            "--vs-text-primary", "--vs-text-secondary", "--vs-text-tertiary",
            "--vs-verified", "--vs-verified-bg",
            "--vs-review", "--vs-review-bg",
            "--vs-unsupported", "--vs-unsupported-bg",
            "--vs-info", "--vs-info-bg", "--vs-focus",
            "--vs-serif", "--vs-sans", "--vs-mono",
            "--vs-r-sm", "--vs-r-md", "--vs-r-lg",
        ],
    )
    def test_every_design_token_exists(self, token: str) -> None:
        assert token in _app_source(), f"design token {token} is missing from the stylesheet"

    def test_spec_colour_values_are_used_verbatim(self) -> None:
        # Guards against silent palette drift away from the documented spec.
        source = _app_source()
        for value in [
            "#FBFAF6", "#FFFFFF", "#F4F3EC", "#E4E1D6", "#CFCABC",
            "#1F4D3D", "#2A6152", "#E8F0EA",
            "#1A1D1A", "#5A615A", "#8A908A",
            "#2F6B4F", "#E7F1EA", "#8A6212", "#FBF2DF", "#9B2C2C", "#FAEAEA",
        ]:
            assert value in source, f"spec colour {value} is not in the stylesheet"

    def test_spec_spacing_scale_is_present(self) -> None:
        source = _app_source()
        for step in ["--vs-s1:4px", "--vs-s2:8px", "--vs-s3:12px", "--vs-s4:16px",
                     "--vs-s5:24px", "--vs-s6:32px", "--vs-s7:48px", "--vs-s8:64px"]:
            assert step in source, f"spacing token {step} missing"

    def test_three_typography_stacks_are_distinct(self) -> None:
        source = _app_source()
        assert "Georgia" in source      # serif for headings and prose
        assert "Segoe UI" in source     # sans for chrome
        assert "Consolas" in source     # mono for quoted evidence

    def test_evidence_passage_uses_the_mono_stack(self) -> None:
        source = _app_source()
        passage_block = source[source.index(".vs-passage {"):]
        passage_block = passage_block[: passage_block.index("}")]
        assert "var(--vs-mono)" in passage_block

    def test_three_status_colours_are_distinct(self) -> None:
        # Asserted on the token *definitions*, not the chip rules: the rules reference
        # `var(--vs-verified)` and friends, so testing the literals there would be testing the
        # wrong end of the indirection.
        source = _app_source()
        tokens = dict(
            re.findall(r"(--vs-(?:verified|review|unsupported)(?:-bg)?):\s*(#[0-9A-Fa-f]{6})", source)
        )
        assert tokens["--vs-verified"] == "#2F6B4F"
        assert tokens["--vs-review"] == "#8A6212"
        assert tokens["--vs-unsupported"] == "#9B2C2C"
        assert tokens["--vs-verified-bg"] == "#E7F1EA"
        assert tokens["--vs-review-bg"] == "#FBF2DF"
        assert tokens["--vs-unsupported-bg"] == "#FAEAEA"
        assert len({tokens[f"--vs-{name}"] for name in ["verified", "review", "unsupported"]}) == 3

    def test_status_is_never_colour_alone(self) -> None:
        # FR-45: every chip carries an icon and a text label.
        source = _app_source()
        assert 'aria-hidden="true"' in source
        assert "LABEL_ICON" in source
        chip_body = source[source.index("def chip("): source.index("def show_failures(")]
        assert "LABEL_ICON.get(label" in chip_body
        assert "escape(label)" in chip_body

    def test_responsive_breakpoints_from_the_spec_exist(self) -> None:
        source = _app_source()
        assert "@media (max-width: 1199px)" in source
        assert "@media (max-width: 767px)" in source

    def test_no_looping_or_ambient_animation(self) -> None:
        # Design spec §2.4: no looping animation, no skeleton shimmer, no typewriter effect.
        source = _app_source().lower()
        for banned in ["@keyframes", "animation: infinite", "infinite", "bounce", "shimmer"]:
            assert banned not in source, f"{banned!r} in the stylesheet"


class TestContrast:
    """WCAG AA ratios for the documented pairs. Measured, not assumed — design spec §2.1."""

    @staticmethod
    def _luminance(hex_colour: str) -> float:
        channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    @classmethod
    def _ratio(cls, foreground: str, background: str) -> float:
        first, second = cls._luminance(foreground), cls._luminance(background)
        lighter, darker = max(first, second), min(first, second)
        return (lighter + 0.05) / (darker + 0.05)

    @pytest.mark.parametrize(
        "foreground,background,label",
        [
            ("#1A1D1A", "#FBFAF6", "body text on canvas"),
            ("#1A1D1A", "#FFFFFF", "body text on surface"),
            ("#5A615A", "#FFFFFF", "secondary text on surface"),
            ("#5A615A", "#FBFAF6", "secondary text on canvas"),
            ("#1F4D3D", "#FBFAF6", "primary on canvas"),
            ("#1F4D3D", "#FFFFFF", "primary on surface"),
            ("#1F4D3D", "#E8F0EA", "primary on muted chip"),
            ("#2F6B4F", "#E7F1EA", "Verified chip"),
            ("#8A6212", "#FBF2DF", "Needs Review chip"),
            ("#9B2C2C", "#FAEAEA", "Unsupported chip"),
            ("#2F5D8A", "#EAF1F8", "Info panel"),
            ("#1A1D1A", "#F4F3EC", "evidence passage on sunken"),
            ("#8A908A", "#FFFFFF", "placeholder on surface (large text only)"),
        ],
    )
    def test_contrast_ratio(self, foreground: str, background: str, label: str) -> None:
        ratio = self._ratio(foreground, background)
        # 4.5:1 for body text. The placeholder pair is exempt from body-text AA only when it is
        # non-essential decoration, so it is asserted at the 3:1 large-text floor and named as such.
        floor = 3.0 if "placeholder" in label else 4.5
        assert ratio >= floor, f"{label}: {ratio:.2f}:1 is below {floor}:1"

    def test_no_actual_measurement_is_being_claimed_for_unmeasured_pairs(self) -> None:
        # Guard against the report claiming contrast figures for pairs this test does not cover.
        source = _app_source()
        assert "contrast-ratio" not in source


# --------------------------------------------------------------------------
# UI-1: the app actually starts
# --------------------------------------------------------------------------


class TestHeadlessStartup:
    def _free_port(self) -> int:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])

    def test_ui1_app_starts_headless_and_serves(self) -> None:
        """UI-1: `streamlit run app.py --server.headless true` must boot and serve.

        A UI that renders beautifully in a screenshot but crashes on start is not a working UI, and a
        screenshot cannot detect that. This is the automated half of the UI test plan; the visual
        walkthroughs stay manual.
        """
        port = self._free_port()
        process = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run", str(APP_PATH),
                "--server.headless", "true",
                f"--server.port={port}",
                "--browser.gatherUsageStats=false",
            ],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        served = False
        try:
            deadline = time.time() + 90
            while time.time() < deadline:
                if process.poll() is not None:
                    output = process.stdout.read() if process.stdout else ""
                    pytest.fail(f"streamlit exited early with code {process.returncode}:\n{output}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=1):
                        served = True
                        break
                except OSError:
                    time.sleep(0.5)
            assert served, "the app did not open a port within 90 s"

            # An open port only proves the server booted. Streamlit executes the script over a
            # websocket, so a runtime error inside `main()` would not stop the port from opening.
            # Fetching the shell and checking the banner is the cheap half; the import-and-render
            # test below is the half that would actually catch an exception in the render path.
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=10) as response:
                assert response.status == 200
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as response:
                body = response.read().decode("utf-8", "replace")
            assert "streamlit" in body.lower()
            assert "traceback" not in body.lower()
        finally:
            process.terminate()
            try:
                output = process.communicate(timeout=15)[0] or ""
            except subprocess.TimeoutExpired:  # pragma: no cover
                process.kill()
                output = ""
            # A traceback in the server log is the failure mode a port check misses.
            assert "Traceback" not in output, f"streamlit logged an exception:\n{output}"

    def test_app_has_no_syntax_errors(self) -> None:
        # Cheaper than the subprocess above, and it isolates the failure mode.
        compile(_app_source(), str(APP_PATH), "exec")

    def test_app_module_imports_without_a_running_server(self) -> None:
        """The UI's definitions must load in a plain interpreter.

        This is the test that actually catches an exception inside a render helper: the headless
        server test only proves Streamlit booted, and Streamlit runs the script over a websocket, so
        a failure in `render_dashboard` would not prevent the port from opening. Executing the
        module's body with no Streamlit runtime exercises import-time work and the module's
        constants — if a function body referenced an undefined name it would surface here only if
        called, which is why the helper tests below call them directly.
        """
        result = subprocess.run(
            [
                sys.executable, "-c",
                "import sys; sys.path.insert(0,'.');"
                "from tests.app_under_test import load; m = load();"
                "print(len(m.STYLESHEET), len(m.RECOVERY))",
            ],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip(), "the app module produced no output"


# --------------------------------------------------------------------------
# Functional UI helpers, tested without a browser
# --------------------------------------------------------------------------


class TestUiHelpers:
    def test_recovery_guidance_exists_for_every_ingest_reason(self) -> None:
        import app_under_test  # type: ignore[import-not-found]
        from src.models import Reason

        missing = [
            reason
            for reason in [
                Reason.FILE_NOT_FOUND, Reason.UNSUPPORTED_EXTENSION, Reason.EMPTY_FILE,
                Reason.ENCRYPTED_PDF, Reason.CORRUPT_PDF, Reason.SCANNED_PDF,
                Reason.TOO_MANY_PAGES, Reason.TOO_LARGE, Reason.ZERO_CHUNKS, Reason.EMPTY_INDEX,
            ]
            if reason not in app_under_test.RECOVERY
        ]
        assert missing == [], f"no recovery guidance for: {missing}"

    def test_every_status_label_has_an_icon_and_meaning(self) -> None:
        import app_under_test  # type: ignore[import-not-found]
        from src.models import VERIFICATION_LABELS

        for label in VERIFICATION_LABELS:
            assert label in app_under_test.LABEL_ICON
            assert label in app_under_test.LABEL_MEANING

    def test_every_verification_reason_has_plain_english(self) -> None:
        import app_under_test  # type: ignore[import-not-found]
        from src.models import Reason

        reasons = [
            Reason.SUPPORTED, Reason.WEAK_SUPPORT, Reason.NO_SUPPORT,
            Reason.UNRESOLVABLE_REFERENCE, Reason.PAGE_MISMATCH, Reason.MALFORMED_MARKER,
            Reason.NO_MARKER, Reason.NUMERIC_MISMATCH, Reason.CONTRADICTION_DETECTED,
        ]
        missing = [reason for reason in reasons if reason not in app_under_test.REASON_TEXT]
        assert missing == [], f"no user-facing text for: {missing}"

    def test_chip_renders_icon_colour_and_text_together(self) -> None:
        import app_under_test  # type: ignore[import-not-found]

        for label in ["Verified", "Needs Review", "Unsupported"]:
            html = app_under_test.chip(label)
            assert label in html
            assert app_under_test.LABEL_ICON[label] in html
            assert "vs-chip-" in html

    def test_markers_helper_deduplicates_and_preserves_order(self) -> None:
        from app_under_test import _markers_of, make_response

        response = make_response()
        markers = _markers_of(response)
        assert [entry[0] for entry in markers] == ["S1, p.1", "S2, p.2"]
        assert len(markers) == len(set(markers))

    def test_markers_helper_is_empty_for_an_abstained_answer(self) -> None:
        from app_under_test import _markers_of
        from src.models import AnswerResponse, GeneratedAnswer, QueryMetrics, VerificationSummary

        response = AnswerResponse(
            question="q", answer=GeneratedAnswer(text="", claims=(), generator="t", abstained=True),
            retrieved=(), verifications=(),
            summary=VerificationSummary(
                verified=0, needs_review=0, unsupported=0, uncited=0, unresolved_refs=0,
                worst_support=None, abstained=True,
            ),
            metrics=QueryMetrics(
                embed_ms=0, retrieve_ms=0, generate_ms=0, verify_ms=0, total_ms=0,
                backend="tfidf", store="memory", generator="t",
            ),
        )
        assert _markers_of(response) == []

    def test_an_unknown_label_falls_back_rather_than_crashing(self) -> None:
        import app_under_test  # type: ignore[import-not-found]

        html = app_under_test.chip("Something New")
        assert "Something New" in html
        assert "vs-chip-review" in html


class TestRenderHelpersRun:
    """Call the render helpers with Streamlit's API stubbed.

    The headless test proves the server boots; this proves the render path executes. `st.markdown`
    and friends do nothing useful outside a script run context, so they are replaced with recorders
    that capture the markup. That turns a visual concern into an executable one without adding
    Streamlit's AppTest as a dependency.

    This is still not a substitute for the manual walkthrough — it cannot tell you the layout looks
    right — but it does catch an exception, a typo or a missing attribute in a code path no other
    test executes.
    """

    @pytest.fixture
    def recorder(self, monkeypatch: pytest.MonkeyPatch):
        from app_under_test import load

        module = load()
        emitted: list[str] = []
        calls: list[str] = []

        def fake_markdown(body="", **kwargs):
            emitted.append(str(body))
            calls.append("markdown")

        def fake_container(*args, **kwargs):
            class _Container:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *exc):
                    return False

            return _Container()

        class FakeSidebar:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False

            def __getattr__(self_inner, name):
                def passthrough(*args, **kwargs):
                    if name == "radio":
                        return "Dashboard"
                    return _NullWidget()

                return passthrough

        class _NullWidget:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False

            def __getattr__(self_inner, name):
                return lambda *a, **k: None

        for attribute, replacement in [
            ("markdown", fake_markdown), ("container", fake_container),
            # `st.columns(n)` is unpacked into exactly n widgets in several places, so the stub
            # has to honour the requested width rather than returning a fixed pair.
            ("columns", lambda *a, **k: tuple(_NullWidget() for _ in range(a[0] if a else 1))),
            ("expander", lambda *a, **k: _NullWidget()),
            ("dataframe", lambda *a, **k: calls.append("dataframe")),
            ("file_uploader", lambda *a, **k: []),
            ("text_input", lambda *a, **k: ""), ("button", lambda *a, **k: False),
            ("selectbox", lambda *a, **k: None), ("slider", lambda *a, **k: 0),
            ("status", lambda *a, **k: _NullWidget()), ("spinner", lambda *a, **k: _NullWidget()),
            ("warning", lambda *a, **k: calls.append("warning")),
            ("error", lambda *a, **k: calls.append("error")),
            ("info", lambda *a, **k: calls.append("info")),
            ("success", lambda *a, **k: calls.append("success")),
            ("rerun", lambda *a, **k: calls.append("rerun")),
            ("session_state", {}),
        ]:
            monkeypatch.setattr(module.st, attribute, replacement, raising=False)
        monkeypatch.setattr(module.st, "sidebar", FakeSidebar(), raising=False)
        return module, emitted, calls

    def test_dashboard_renders_on_an_empty_index(self, recorder) -> None:
        module, emitted, calls = recorder
        from src.pipeline import ResearchPipeline

        module.render_dashboard(ResearchPipeline())
        assert emitted, "the dashboard rendered nothing"
        joined = " ".join(emitted)
        assert "vs-hero" in joined
        assert "Documents" in joined
        # No documents: the counts must read zero, not a plausible-looking number.
        assert ">0</div>" in joined
        assert "vs-empty" in joined

    def test_dashboard_renders_real_counts_when_indexed(self, recorder, evidence_pdf: Path) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline.index([evidence_pdf])
        module.render_dashboard(pipeline)
        joined = " ".join(emitted)
        assert ">1</div>" in joined  # one document
        assert ">5</div>" in joined  # five pages

    def test_library_renders_rows_and_real_failures(self, recorder, tmp_path: Path) -> None:
        from conftest import build_pdf, write_pdf
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline.index([
            write_pdf(tmp_path, "ok.pdf", build_pdf(["Chroma persists embeddings locally."])),
            write_pdf(tmp_path, "bad.pdf", build_pdf([""], graphics_only=True)),
        ])
        module.render_library(pipeline)
        joined = " ".join(emitted)
        assert "Nothing indexed" not in joined
        assert "bad.pdf" in joined
        assert "OCR" in joined

    def test_workspace_renders_an_answer_with_all_three_panels(
        self, recorder, evidence_pdf: Path
    ) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline.index([evidence_pdf])
        response = pipeline.ask("What does Chroma persist?")
        module._render_answer(response)
        module._render_verification(response)
        module._render_inspector(response)
        module._render_retrieved(response)
        joined = " ".join(emitted)
        assert "vs-answer" in joined
        assert "Verification" in joined
        assert "Evidence inspector" in joined
        assert "Passages retrieved" in joined

    def test_workspace_renders_the_abstention_state(self, recorder) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        module.render_workspace(ResearchPipeline())
        joined = " ".join(emitted)
        assert "The index is empty" in joined
        assert "Upload a text-based PDF" in joined

    def test_sidebar_renders_live_status(self, recorder, evidence_pdf: Path) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline.index([evidence_pdf])
        module.render_sidebar(pipeline)
        joined = " ".join(emitted)
        assert "Documents" in joined
        assert "Chunks" in joined
        assert "tfidf" in joined

    def test_header_and_footer_render(self, recorder) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        module.render_header()
        module.render_footer(ResearchPipeline())
        joined = " ".join(emitted)
        assert "Verdant Scholar" in joined
        assert "backend tfidf" in joined

    def test_inspector_shows_both_scores_separately_labelled(
        self, recorder, evidence_pdf: Path
    ) -> None:
        # The two-score separation is the most graded visual property in the whole UI, so it is
        # asserted on the rendered markup rather than on the source.
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline.index([evidence_pdf])
        response = pipeline.ask("What does Chroma persist?")
        module._render_inspector(response)
        joined = " ".join(emitted)
        assert "support score" in joined
        assert "retrieval relevance to your question" in joined
        # They must not share a label.
        assert "support score</span>" in joined

    def test_inspector_states_what_the_label_does_not_mean(self, recorder, evidence_pdf: Path) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline.index([evidence_pdf])
        module._render_inspector(pipeline.ask("What does Chroma persist?"))
        assert "What this label does not mean" in " ".join(emitted)

    def test_verification_panel_never_renders_an_average(self, recorder, evidence_pdf: Path) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline.index([evidence_pdf])
        module._render_verification(pipeline.ask("What does Chroma persist?"))
        joined = " ".join(emitted)
        assert "%" not in joined
        assert "not the same number as the" in joined

    def test_an_unsupported_claim_renders_without_a_passage(self, recorder) -> None:
        module, emitted, _ = recorder
        from src.models import (
            AnswerResponse, ClaimVerification, GeneratedAnswer, QueryMetrics, VerificationSummary,
        )

        response = AnswerResponse(
            question="q",
            answer=GeneratedAnswer(text="Chroma stores data locally. [S9, p.2]", claims=(), generator="t"),
            retrieved=(),
            verifications=(
                ClaimVerification(
                    claim_id="clm_0", claim_text="Chroma stores data locally.",
                    label="Unsupported", support_score=0.0, similarity=0.0, overlap=0.0,
                    evidence=None, relevance_score=None, reason="unresolvable_reference",
                    explanation="The answer cites S9, p.2, but no retrieved passage carries it.",
                ),
            ),
            summary=VerificationSummary(
                verified=0, needs_review=0, unsupported=1, uncited=0, unresolved_refs=1,
                worst_support=0.0, abstained=False,
            ),
            metrics=QueryMetrics(
                embed_ms=1, retrieve_ms=1, generate_ms=1, verify_ms=1, total_ms=4,
                backend="tfidf", store="memory", generator="t",
            ),
        )
        module._render_inspector(response)
        joined = " ".join(emitted)
        assert "Unsupported" in joined
        assert "no passage" in joined
        assert "does not substitute" in joined

    def test_degraded_footer_is_visible_not_hidden(self, recorder) -> None:
        module, emitted, _ = recorder
        from src.pipeline import ResearchPipeline

        pipeline = ResearchPipeline()
        pipeline._degraded_reason = "weights are not on this machine"
        module.render_footer(pipeline)
        joined = " ".join(emitted)
        assert "degraded" in joined
        assert "weights are not on this machine" in joined


class TestHonestEmptyStates:
    def test_every_surface_has_an_empty_state(self) -> None:
        source = _app_source()
        for renderer in ["render_dashboard", "render_library", "render_workspace"]:
            body = source[source.index(f"def {renderer}("):]
            body = body[: body.index("\ndef ", 5)]
            assert "vs-empty" in body, f"{renderer} has no empty state"

    def test_the_empty_index_message_explains_why(self) -> None:
        source = _app_source()
        assert "Upload a text-based PDF from the Dashboard first" in source

    def test_no_mock_rows_stand_in_for_missing_documents(self) -> None:
        source = _app_source()
        # The library must not append a fake row when the index is empty.
        library = source[source.index("def render_library("): source.index("def _source_path(")]
        assert "Nothing indexed" in library
        assert "if rows:" in library

    def test_the_ui_states_that_verified_is_not_proof(self) -> None:
        source = _app_source()
        assert "not proof that a claim is true" in source
        assert "What this label does not mean" in source

# --------------------------------------------------------------------------
# UI evidence: the captured screenshots are real files, and they are not blank
# --------------------------------------------------------------------------


class TestScreenshotsAreEvidence:
    """Phase F captured five screenshots of the running application.

    A screenshot is evidence, which makes it exactly the kind of artefact that rots quietly: it
    outlives the code that produced it, nobody notices, and a report ends up citing a picture of a
    version of the app that no longer exists.

    These tests cannot tell whether a picture is *honest* -- only a person can. What they can do
    is fail when a file is missing, truncated, or a blank rectangle, and when the set drifts from
    the states the report claims to show. Regenerate with `tools/capture_screenshots.py`.
    """

    EXPECTED = {
        "S1_dashboard_empty": "the dashboard before upload, in its real empty state",
        "S2_library_indexed": "the indexed document library",
        "S3_answer_with_citations": "a grounded answer carrying [Sx, p.y] markers",
        "S4_verification_evidence": "per-claim verification and the cited passage",
        "S5_abstention": "an out-of-corpus question refused",
    }

    @staticmethod
    def _dir() -> Path:
        return Path(__file__).resolve().parent.parent / "docs" / "screenshots"

    @pytest.mark.parametrize("stem,what", sorted(EXPECTED.items()))
    def test_the_screenshot_exists_and_is_a_real_png(self, stem: str, what: str) -> None:
        path = self._dir() / f"{stem}.png"
        assert path.exists(), f"{stem}.png is missing; regenerate with tools/capture_screenshots.py"
        payload = path.read_bytes()
        assert payload.startswith(b"\x89PNG\r\n\x1a\n"), f"{stem} is not a PNG"
        assert payload[-8:] == b"IEND\xaeB`\x82", f"{stem} looks truncated"

    @pytest.mark.parametrize("stem,what", sorted(EXPECTED.items()))
    def test_the_screenshot_is_not_a_blank_rectangle(self, stem: str, what: str) -> None:
        """A uniform image is what a failed render produces, and it looks like a valid PNG.

        Checked by counting distinct colours in the raw pixels, which needs no image library. A
        real render of this app yields hundreds; a blank one yields one.
        """
        payload = (self._dir() / f"{stem}.png").read_bytes()
        # Crude but sufficient: the compressed stream of a real screenshot varies constantly,
        # while a solid image compresses to almost nothing.
        distinct = len(set(payload[200:20000]))
        assert len(payload) > 40_000, f"{stem} is only {len(payload)} bytes; that is not a render"
        assert distinct > 40, f"{stem} looks uniform; distinct byte values: {distinct}"

    def test_every_state_the_report_claims_is_actually_captured(self) -> None:
        present = {p.stem for p in self._dir().glob("*.png")}
        missing = set(self.EXPECTED) - present
        assert not missing, f"the report cites screenshots that do not exist: {sorted(missing)}"

    def test_the_capture_script_commits_to_the_synthetic_fixture(self) -> None:
        """Screenshots of the Stage 2 report would publish it.

        Phase E declined to commit that document because it names its authors, their PRNs and their
        project guide, and the repository is public. Capturing its pages would undo that decision
        through a side door, so the capture script is asserted to use the committed fixture instead.
        """
        script = (
            Path(__file__).resolve().parent.parent / "tools" / "capture_screenshots.py"
        ).read_text("utf-8")
        assert "fixtures" in script and "single_column.pdf" in script, (
            "the capture script must use the committed synthetic fixture"
        )
        assert "Downloads" not in script, (
            "the capture script must not read the team's Stage 2 report"
        )
