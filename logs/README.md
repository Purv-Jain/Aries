# Reproducible logs — Phase 7

Every file here is **captured output from a real command run on this machine on 2026-10-09**. Nothing
is transcribed by hand and nothing is illustrative. To regenerate, run the command named against
each file.

**Environment** (from [01_environment.txt](01_environment.txt)): Windows 11 build 26300,
Intel64 Family 6 Model 154, 8 logical CPUs, CPython 3.14.6, no GPU, `.venv` with 110 packages.
`pip check` → `No broken requirements found.`

| # | File | Command | What it proves |
|---|---|---|---|
| 01 | [01_environment.txt](01_environment.txt) | `python --version`, `platform.platform()`, `pip list --format=freeze` | The interpreter and exact dependency set every other figure was produced on |
| 02 | [02_test_suite_offline.txt](02_test_suite_offline.txt) | `pytest -q -m "not semantic"` with all three `*_OFFLINE=1`, then `pip check` | **429 passed, 6 deselected**, 0 failures, 0 skipped, 0 xfailed |
| 03 | [03_run_demo.txt](03_run_demo.txt) | `run_demo.py --pdf <report> --question "Which sentence splitter…"` | A full index → ask → verify cycle on the real 15-page paper: 15 pages → 46 chunks, 5 claims verified, wall time 0.43 s |
| 04 | [04_measure.txt](04_measure.txt) | `python -X utf8 tools\measure.py` | The 13 measured metrics: Recall@1 0.667, Recall@3+ 1.0, MRR 0.778, indexing 3.236 s/100 pages, query p50 12.40 ms, determinism 1.0, peak RSS 191.3 MB, **abstention 0.0** |
| 05 | [05_evaluate.txt](05_evaluate.txt) | `python -X utf8 tools\evaluate.py --sweep`, then `tools\build_cases.py` | The threshold sweep 0.30→0.90 and the chosen point 0.63; plus `verbatim check: all 24 passages found in the extraction` |
| 06 | [06_ui_headless.txt](06_ui_headless.txt) | `streamlit run app.py --server.headless true --server.port=8611`, then two HTTP requests | Root `status=200 len=6463`, `_stcore/health` → `ok`, `traceback present: False` |
| 07 | [07_abstention_q1.txt](07_abstention_q1.txt) | `run_demo.py --question "What is the boiling point of mercury?"` | **R-24 before/after, question 1 of 3.** The question is not in the corpus; the system answered anyway |
| 08 | [08_abstention_q2.txt](08_abstention_q2.txt) | `run_demo.py --question "Who won the 2019 Cricket World Cup?"` | **R-24, question 2 of 3.** Five claims, all `Verified` at support 1.00 |
| 10 | [10_semantic_suite.txt](10_semantic_suite.txt) | `pytest -q -m semantic` with the weights fetched (`HF_HUB_DISABLE_XET=1`) | **6 passed**, 11–81 s on CPU. First run was 2 passed / 4 failed: `embed_query` returned a 1-D array, `similarity()` handed it to sklearn, and every semantic query raised. Fixed and guarded by 7 weights-free tests |
| 09 | [09_abstention_q3.txt](09_abstention_q3.txt) | `run_demo.py --question "How does photosynthesis convert light energy into chemical energy?"` | **R-24, question 3 of 3** |

## The three logs that matter most

**02** is the reproducibility claim. 449 tests, no network, no model download, on a machine whose only
Python is the pinned one.

**04 and 05** are the measurement claim. Every number in the Stage 3 report appears here first.

**07, 08, 09** are the negative result, captured the same way as the positive ones. All three questions
are absent from the corpus, and the system answered all three with real citations to irrelevant
passages — 0.000 abstention. These files exist so that R-24 cannot be quietly softened in the report
into a footnote about "some edge cases". It is a reproducible failure of a documented behaviour, and
[docs/14_RISK_REGISTER.md](../docs/14_RISK_REGISTER.md) carries the analysis.

## One caveat on these numbers

Latency and RSS vary run to run; that is why 04 reports medians over 3 indexing runs and percentiles
over 27 queries rather than single figures. Recall, MRR, marker coverage and the calibration results
are deterministic on this fixture and reproduce exactly. The six `deselected` tests in 02 are the
`semantic`-marked ones: **never run**, because no MiniLM or FLAN-T5 weights exist on this machine.