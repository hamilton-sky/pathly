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


def test_help_suggests_init_when_no_plans_exist(tmp_path, capsys):
    result = cli.main(["--project-dir", str(tmp_path), "help"])

    assert result == 0
    output = capsys.readouterr().out
    assert "plans/: missing" in output
    assert "pathly init <feature>" in output
    assert "pathly doctor" in output


def test_help_suggests_next_actions_for_existing_plan(tmp_path, capsys):
    cli.main(["--project-dir", str(tmp_path), "init", "checkout-flow"])
    capsys.readouterr()

    result = cli.main(["--project-dir", str(tmp_path), "help"])

    assert result == 0
    output = capsys.readouterr().out
    assert "plans/: ok" in output
    assert "checkout-flow: has PROGRESS.md" in output
    assert "pathly run checkout-flow --entry build" in output


def test_go_suggests_flow_command(tmp_path, capsys):
    result = cli.main(["--project-dir", str(tmp_path), "go", "add", "password", "reset"])

    assert result == 0
    output = capsys.readouterr().out
    assert "Pathly go" in output
    assert "pathly flow add-password-reset" in output


def test_flow_alias_uses_team_flow_root(tmp_path, monkeypatch):
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

    result = cli.main(["--project-dir", str(tmp_path), "flow", "checkout-flow", "--entry", "test"])

    assert result == 0
    assert seen == {
        "feature": "checkout-flow",
        "mode": "interactive",
        "entry": "test",
        "root": Path(tmp_path).resolve(),
        "ran": True,
    }


def test_debug_explore_and_review_are_exposed(tmp_path, capsys):
    assert cli.main(["--project-dir", str(tmp_path), "debug", "checkout", "fails"]) == 0
    assert "Use Pathly to debug checkout fails" in capsys.readouterr().out

    assert cli.main(["--project-dir", str(tmp_path), "explore", "auth", "flow"]) == 0
    assert "Use Pathly to explore auth flow" in capsys.readouterr().out

    assert cli.main(["--project-dir", str(tmp_path), "review"]) == 0
    assert "Use Pathly review" in capsys.readouterr().out


def test_install_codex_prints_complete_marketplace_setup(capsys):
    result = cli.main(["install", "codex"])

    assert result == 0
    output = capsys.readouterr().out
    assert "pathly-local" in output
    assert "marketplace.json" in output
    assert "$plugin\\skills" in output
    assert '"path": "./plugins/pathly"' in output
    assert "codex plugin marketplace add $market" in output
    assert "globally on this machine" in output


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
