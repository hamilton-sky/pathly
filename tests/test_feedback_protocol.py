"""Protocol alignment test: ensures the Python FeedbackFile constants and
the Markdown skill definitions agree on feedback file names.

This is the seam between the Python FSM runtime (pathly-engine) and the
agent/skill behavioral contracts (pathly-adapters). If the file names drift
apart, the Python orchestrator will handle files the agents never create, or
vice versa.

Run with: pytest tests/test_feedback_protocol.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = REPO_ROOT / "pathly-engine"
ADAPTERS_ROOT = REPO_ROOT / "pathly-adapters"

sys.path.insert(0, str(ENGINE_ROOT))


# ---------------------------------------------------------------------------
# Ground truth: FeedbackFile constants from the Python FSM
# ---------------------------------------------------------------------------

def _load_feedback_file_constants() -> set[str]:
    from orchestrator.constants import FeedbackFile
    return {
        v for k, v in vars(FeedbackFile).items()
        if not k.startswith("_") and isinstance(v, str) and v.endswith(".md")
    }


# ---------------------------------------------------------------------------
# Extract file names referenced in Markdown skill/agent files
# ---------------------------------------------------------------------------

def _md_files_in(*dirs: Path) -> list[Path]:
    result = []
    for d in dirs:
        result.extend(d.glob("**/*.md"))
    return result


_FEEDBACK_FILENAME_PATTERN = re.compile(
    r'\b([A-Z_]+\.md)\b'
)

_KNOWN_FEEDBACK_SUFFIXES = {
    "ARCH_FEEDBACK.md",
    "REVIEW_FAILURES.md",
    "IMPL_QUESTIONS.md",
    "DESIGN_QUESTIONS.md",
    "TEST_FAILURES.md",
    "HUMAN_QUESTIONS.md",
}


def _extract_feedback_names_from_md(path: Path) -> set[str]:
    """Return all UPPER_CASE.md filenames found in a Markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    found = set(_FEEDBACK_FILENAME_PATTERN.findall(text))
    # Keep only names that look like feedback files (all-caps, .md suffix)
    return {name for name in found if name == name.upper()}


def _all_feedback_names_in_docs() -> set[str]:
    skill_dir = ADAPTERS_ROOT / "core" / "skills"
    agent_dir = ADAPTERS_ROOT / "core" / "agents"
    docs_dir = REPO_ROOT / "docs"

    all_names: set[str] = set()
    for md_file in _md_files_in(skill_dir, agent_dir, docs_dir):
        all_names |= _extract_feedback_names_from_md(md_file)

    # Restrict to names that overlap with known feedback file patterns
    return all_names & _KNOWN_FEEDBACK_SUFFIXES


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFeedbackProtocolAlignment:
    """Verify that Python constants and Markdown contracts reference the same files."""

    def test_all_python_constants_appear_in_docs(self):
        """Every FeedbackFile constant must be mentioned in at least one skill/agent/doc file."""
        constants = _load_feedback_file_constants()
        in_docs = _all_feedback_names_in_docs()

        missing = constants - in_docs
        assert not missing, (
            "These FeedbackFile constants from orchestrator/constants.py are NOT mentioned "
            "in any skill, agent, or docs Markdown file. "
            "Update the docs or remove the constant:\n"
            + "\n".join(f"  - {name}" for name in sorted(missing))
        )

    def test_no_undeclared_feedback_names_in_docs(self):
        """Every feedback filename mentioned in docs must exist as a Python constant."""
        constants = _load_feedback_file_constants()
        in_docs = _all_feedback_names_in_docs()

        undeclared = in_docs - constants
        assert not undeclared, (
            "These feedback filenames appear in Markdown docs but have NO matching "
            "FeedbackFile constant in orchestrator/constants.py. "
            "Add the constant or fix the typo in the docs:\n"
            + "\n".join(f"  - {name}" for name in sorted(undeclared))
        )

    def test_feedback_constants_are_all_md_files(self):
        """All FeedbackFile constants must end with .md (catches copy/paste errors)."""
        constants = _load_feedback_file_constants()
        bad = {name for name in constants if not name.endswith(".md")}
        assert not bad, (
            "FeedbackFile constants that do not end with .md:\n"
            + "\n".join(f"  - {name}" for name in sorted(bad))
        )

    def test_feedback_constants_are_uppercase(self):
        """FeedbackFile names must be UPPER_CASE (convention across the protocol)."""
        constants = _load_feedback_file_constants()
        bad = {name for name in constants if name != name.upper()}
        assert not bad, (
            "FeedbackFile constants that are not UPPER_CASE.md:\n"
            + "\n".join(f"  - {name}" for name in sorted(bad))
        )

    def test_six_canonical_feedback_files_exist(self):
        """Smoke-check: the six canonical feedback files defined in the protocol must all be present."""
        constants = _load_feedback_file_constants()
        expected = {
            "ARCH_FEEDBACK.md",
            "REVIEW_FAILURES.md",
            "IMPL_QUESTIONS.md",
            "DESIGN_QUESTIONS.md",
            "TEST_FAILURES.md",
            "HUMAN_QUESTIONS.md",
        }
        missing = expected - constants
        assert not missing, (
            "These canonical feedback files are missing from FeedbackFile constants:\n"
            + "\n".join(f"  - {name}" for name in sorted(missing))
        )
