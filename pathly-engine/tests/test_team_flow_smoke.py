"""Smoke tests for the Python team-flow driver."""

import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.constants import FeedbackFile, FSMState, Mode
from orchestrator.state import State
import team_flow
from runners import ClaudeRunner, CodexRunner


REPO_ROOT = Path(__file__).resolve().parents[1]

CORE_PLAN_FILES = {
    "USER_STORIES.md": "# User Stories\n",
    "IMPLEMENTATION_PLAN.md": "# Implementation Plan\n",
    "PROGRESS.md": "# Progress\n\n| Conversation | Status |\n|---|---|\n| 1 | DONE |\n",
    "CONVERSATION_PROMPTS.md": "# Conversation Prompts\n",
}


def test_team_flow_package_runs_as_module():
    result = subprocess.run(
        [sys.executable, "-m", "team_flow", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "FSM-driven pipeline driver" in result.stdout


def make_driver(tmp_path, monkeypatch, feature="demo", entry="build"):
    return team_flow.Driver(feature=feature, mode=Mode.INTERACTIVE, entry=entry, repo_root=tmp_path)


def write_plan(root, feature="demo", files=None):
    plan_dir = root / "plans" / feature
    plan_dir.mkdir(parents=True, exist_ok=True)
    for name, content in (files or CORE_PLAN_FILES).items():
        (plan_dir / name).write_text(content, encoding="utf-8")
    return plan_dir


def test_lite_build_entry_accepts_four_core_plan_files(tmp_path, monkeypatch):
    """Build entry should match lite docs: only the 4 core files are required."""
    write_plan(tmp_path)
    driver = make_driver(tmp_path, monkeypatch, entry="build")

    driver.skip_to_entry()

    assert driver.state.current == FSMState.BUILDING


def test_build_entry_rejects_missing_core_plan_file(tmp_path, monkeypatch, capsys):
    """Build entry fails fast when one of the 4 core files is missing."""
    files = dict(CORE_PLAN_FILES)
    files.pop("CONVERSATION_PROMPTS.md")
    write_plan(tmp_path, files=files)
    driver = make_driver(tmp_path, monkeypatch, entry="build")

    with pytest.raises(SystemExit):
        driver.skip_to_entry()

    assert "CONVERSATION_PROMPTS.md" in capsys.readouterr().out


def test_test_entry_rejects_unfinished_conversations(tmp_path, monkeypatch):
    """Test entry must not run while PROGRESS.md still has TODO rows."""
    files = dict(CORE_PLAN_FILES)
    files["PROGRESS.md"] = "# Progress\n\n| Conversation | Status |\n|---|---|\n| 1 | TODO |\n"
    write_plan(tmp_path, files=files)
    driver = make_driver(tmp_path, monkeypatch, entry="test")

    with pytest.raises(SystemExit):
        driver.skip_to_entry()


def test_test_entry_accepts_complete_lite_plan(tmp_path, monkeypatch):
    """Test entry can fast-forward a completed lite plan to TESTING."""
    write_plan(tmp_path)
    driver = make_driver(tmp_path, monkeypatch, entry="test")

    driver.skip_to_entry()

    assert driver.state.current == FSMState.TESTING


def test_runner_selection_defaults_to_claude_and_honors_env(tmp_path, monkeypatch):
    monkeypatch.delenv("PATHLY_RUNNER", raising=False)
    driver = make_driver(tmp_path, monkeypatch)

    assert isinstance(driver.runner, ClaudeRunner)

    monkeypatch.setenv("PATHLY_RUNNER", "auto")
    monkeypatch.setattr(ClaudeRunner, "is_available", lambda self: True)
    driver = make_driver(tmp_path, monkeypatch)

    assert isinstance(driver.runner, ClaudeRunner)

    monkeypatch.setenv("PATHLY_RUNNER", "codex")
    driver = make_driver(tmp_path, monkeypatch)

    assert isinstance(driver.runner, CodexRunner)

    driver = team_flow.Driver(
        feature="demo",
        mode=Mode.INTERACTIVE,
        entry="build",
        repo_root=tmp_path,
        runner="claude",
    )

    assert isinstance(driver.runner, ClaudeRunner)


def test_runner_auto_falls_back_to_codex_when_claude_is_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("PATHLY_RUNNER", "auto")
    monkeypatch.setattr(ClaudeRunner, "is_available", lambda self: False)
    monkeypatch.setattr(CodexRunner, "is_available", lambda self: True)

    driver = make_driver(tmp_path, monkeypatch)

    assert isinstance(driver.runner, CodexRunner)


def test_feedback_file_create_and_delete_blocks_then_resumes(tmp_path, monkeypatch):
    """Feedback file appearance blocks the FSM; deletion resumes previous state."""
    write_plan(tmp_path)
    driver = make_driver(tmp_path, monkeypatch, entry="build")
    driver.state = State(current=FSMState.BUILDING)

    driver.check_feedback_changes(set(), {FeedbackFile.REVIEW_FAILURES})

    assert driver.state.current == FSMState.BLOCKED_ON_FEEDBACK
    assert driver.state.active_feedback_file == FeedbackFile.REVIEW_FAILURES

    driver.check_feedback_changes({FeedbackFile.REVIEW_FAILURES}, set())

    assert driver.state.current == FSMState.BUILDING
    assert driver.state.active_feedback_file is None


def test_unsafe_feature_name_raises_value_error(tmp_path, monkeypatch):
    """DriverConfig must reject feature names that could escape plans/."""
    import pytest
    from team_flow.config import DriverConfig
    from orchestrator.constants import Mode

    for bad_name in ("../../.env", "foo/bar", "foo\\bar", "a..b", ""):
        with pytest.raises(ValueError):
            DriverConfig(repo_root=tmp_path, feature=bad_name, mode=Mode.INTERACTIVE, entry="build")


def test_review_feedback_zero_diff_escalates_to_human(tmp_path, monkeypatch):
    """A review-fix pass with no git diff should escalate instead of looping."""
    plan_dir = write_plan(tmp_path)
    feedback_dir = plan_dir / "feedback"
    feedback_dir.mkdir()
    (feedback_dir / FeedbackFile.REVIEW_FAILURES).write_text(
        "[IMPL] demo.py:1 - violation - fix required\n",
        encoding="utf-8",
    )
    driver = make_driver(tmp_path, monkeypatch, entry="build")
    driver.state = State(
        current=FSMState.BLOCKED_ON_FEEDBACK,
        active_feedback_file=FeedbackFile.REVIEW_FAILURES,
        state_stack=[FSMState.REVIEWING],
    )
    monkeypatch.setattr(driver, "run_claude", lambda prompt: (0, {}))
    monkeypatch.setattr(driver, "get_git_diff", lambda: "")

    with pytest.raises(SystemExit):
        driver._handle_feedback()

    assert (feedback_dir / FeedbackFile.HUMAN_QUESTIONS).exists()
    assert driver.state.current == FSMState.BLOCKED_ON_HUMAN
