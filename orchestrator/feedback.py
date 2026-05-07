"""Feedback file discovery and priority helpers."""

from __future__ import annotations

from pathlib import Path

from orchestrator.constants import FeedbackFile


FEEDBACK_PRIORITY = [
    FeedbackFile.HUMAN_QUESTIONS,
    FeedbackFile.ARCH_FEEDBACK,
    FeedbackFile.DESIGN_QUESTIONS,
    FeedbackFile.IMPL_QUESTIONS,
    FeedbackFile.REVIEW_FAILURES,
    FeedbackFile.TEST_FAILURES,
]


def open_feedback_files(feedback_dir: Path) -> set[str]:
    """Return markdown feedback filenames currently open on disk."""
    if not feedback_dir.exists():
        return set()
    return {path.name for path in feedback_dir.iterdir() if path.suffix == ".md"}


def highest_priority_feedback(
    open_files: set[str],
    include_human: bool = True,
) -> str | None:
    """Return the highest-priority known feedback file from a set of filenames."""
    for feedback_file in FEEDBACK_PRIORITY:
        if not include_human and feedback_file == FeedbackFile.HUMAN_QUESTIONS:
            continue
        if feedback_file in open_files:
            return feedback_file
    return None
