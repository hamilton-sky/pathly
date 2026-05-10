"""Tests for feedback file discovery and priority helpers."""

import shutil
from pathlib import Path

from orchestrator.constants import FeedbackFile
from orchestrator.feedback import highest_priority_feedback, open_feedback_files


def test_open_feedback_files_returns_empty_for_missing_directory():
    assert open_feedback_files(Path("missing-feedback-dir")) == set()


def test_highest_priority_feedback_uses_known_priority_order():
    open_files = {
        FeedbackFile.TEST_FAILURES,
        FeedbackFile.REVIEW_FAILURES,
        FeedbackFile.ARCH_FEEDBACK,
    }

    assert highest_priority_feedback(open_files) == FeedbackFile.ARCH_FEEDBACK


def test_highest_priority_feedback_can_skip_human_questions():
    open_files = {
        FeedbackFile.HUMAN_QUESTIONS,
        FeedbackFile.REVIEW_FAILURES,
    }

    assert (
        highest_priority_feedback(open_files, include_human=False)
        == FeedbackFile.REVIEW_FAILURES
    )


def test_unknown_markdown_files_do_not_outrank_known_feedback_files():
    feedback_dir = Path.cwd() / ".pytest-feedback-test"
    if feedback_dir.exists():
        shutil.rmtree(feedback_dir)
    feedback_dir.mkdir()
    try:
        (feedback_dir / "ZZZ_CUSTOM.md").write_text("custom\n", encoding="utf-8")
        (feedback_dir / FeedbackFile.TEST_FAILURES).write_text("test\n", encoding="utf-8")

        open_files = open_feedback_files(feedback_dir)

        assert "ZZZ_CUSTOM.md" in open_files
        assert highest_priority_feedback(open_files) == FeedbackFile.TEST_FAILURES
    finally:
        shutil.rmtree(feedback_dir, ignore_errors=True)
