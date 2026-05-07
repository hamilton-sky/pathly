"""Candidate Pathly CLI entry point.

The real package entry point still targets ``pathly/cli.py``. This candidate
loads the split implementation under ``pathly/cli/`` without changing the
legacy ``import pathly.cli`` behavior.
"""

from __future__ import annotations

import sys
import importlib.util
from pathlib import Path


CLI_DIR = Path(__file__).with_name("cli")
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

_spec = importlib.util.spec_from_file_location("_pathly_cli_candidate_manager", CLI_DIR / "manager.py")
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load candidate CLI manager from {CLI_DIR}")
_manager = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_manager)

build_parser = _manager.build_parser
main = _manager.main


if __name__ == "__main__":
    raise SystemExit(main())
