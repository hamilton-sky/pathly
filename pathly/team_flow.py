"""Candidate Pathly team-flow runtime entry point.

The legacy runtime still lives at ``scripts/team_flow.py``. This candidate
loads the split implementation under ``pathly/team_flow/`` without changing the
legacy script import path.
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pathly.team_flow.manager import Driver, TeamFlowDriver, build_parser, main


if __name__ == "__main__":
    main()
