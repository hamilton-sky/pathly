"""Candidate Pathly CLI entry point.

The real package entry point still targets ``pathly/cli.py``. This candidate
loads the split implementation under ``pathly/cli/`` without changing the
legacy ``import pathly.cli`` behavior.
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pathly.cli.manager import build_parser, main


if __name__ == "__main__":
    raise SystemExit(main())
