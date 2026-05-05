"""Smoke tests for the public Pathly CLI."""

from pathlib import Path

from pathly import cli
from scripts import team_flow


def test_init_creates_core_plan_files(tmp_path):
    result = cli.main(["--project-dir", str(tmp_path), "init", "checkout-flow"])

    assert result == 0
    plan_dir = tmp_path / "plans" / "checkout-flow"
    assert (plan_dir / "USER_STORIES.md").exists()
    assert (plan_dir / "IMPLEMENTATION_PLAN.md").exists()
    assert (plan_dir / "PROGRESS.md").exists()
    assert (plan_dir / "CONVERSATION_PROMPTS.md").exists()


def test_run_uses_current_project_as_team_flow_root(tmp_path, monkeypatch):
    seen = {}

    class FakeDriver:
        def __init__(self, feature, mode, entry):
            seen["feature"] = feature
            seen["mode"] = mode
            seen["entry"] = entry
            seen["root"] = team_flow.REPO_ROOT

        def run(self):
            seen["ran"] = True

    monkeypatch.setattr(team_flow, "Driver", FakeDriver)

    result = cli.main(["--project-dir", str(tmp_path), "run", "checkout-flow", "--entry", "build", "--fast"])

    assert result == 0
    assert seen == {
        "feature": "checkout-flow",
        "mode": "fast",
        "entry": "build",
        "root": Path(tmp_path).resolve(),
        "ran": True,
    }
