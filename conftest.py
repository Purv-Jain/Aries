"""Make the project root importable regardless of how pytest is invoked.

``python -m pytest`` puts the working directory on ``sys.path``; a bare ``pytest``
does not. Without this file the suite passes only under the first invocation, which
is exactly the kind of quiet environment dependency that breaks CI later. The CI
workflow in docs/09_TESTING_STRATEGY.md runs a bare ``pytest -q``.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))