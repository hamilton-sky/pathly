"""Candidate Pathly team-flow runtime entry point.

The legacy runtime still lives at ``scripts/team_flow.py``. This candidate
loads the split implementation under ``pathly/team_flow/`` without changing the
legacy script import path.
"""

from __future__ import annotations

import sys
import importlib.util
from pathlib import Path


TEAM_FLOW_DIR = Path(__file__).with_name("team_flow")
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TEAM_FLOW_DIR) not in sys.path:
    sys.path.insert(0, str(TEAM_FLOW_DIR))

_spec = importlib.util.spec_from_file_location(
    "_pathly_team_flow_candidate_manager",
    TEAM_FLOW_DIR / "manager.py",
)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load candidate team-flow manager from {TEAM_FLOW_DIR}")
_manager = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_manager)

Driver = _manager.Driver
TeamFlowDriver = _manager.TeamFlowDriver
build_parser = _manager.build_parser
main = _manager.main


if __name__ == "__main__":
    main()
