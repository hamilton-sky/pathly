"""Smoke tests for the public Pathly CLI."""

import subprocess
import sys
from pathlib import Path

import pytest

from pathly import cli, team_flow
from pathly.cli import constants, meet_command
from pathly.cli.installers import codex as codex_installer


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_package_runs_as_module():
    result = subprocess.run(
        [sys.executable, "-m", "pathly.cli", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Pathly: guided agent workflows" in result.stdout


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
    assert "No active feature found" in output
    assert "[1] Brainstorm/refine an unclear idea" in output
    assert "[5] See all commands" in output


def test_help_shows_build_done_menu_for_existing_empty_plan(tmp_path, capsys):
    cli.main(["--project-dir", str(tmp_path), "init", "checkout-flow"])
    capsys.readouterr()

    result = cli.main(["--project-dir", str(tmp_path), "help"])

    assert result == 0
    output = capsys.readouterr().out
    assert "checkout-flow - All conversations complete" in output
    assert "Rigor: lite" in output
    assert "[1] Run tests" in output
    assert "[2] Run tests + retro" in output
    assert "[3] Write retro only          -> retro checkout-flow" in output
    assert "Reply with 1-4:" in output


def test_help_shows_plan_done_menu_when_progress_has_remaining_work(tmp_path, capsys):
    cli.main(["--project-dir", str(tmp_path), "init", "checkout-flow"])
    progress = tmp_path / "plans" / "checkout-flow" / "PROGRESS.md"
    progress.write_text(
        "# Progress\n\n| Conversation | Status |\n|---|---|\n| 1 | DONE |\n| 2 | TODO |\n",
        encoding="utf-8",
    )
    capsys.readouterr()

    result = cli.main(["--project-dir", str(tmp_path), "help"])

    assert result == 0
    output = capsys.readouterr().out
    assert "checkout-flow - Plan ready" in output
    assert "Conv: 1 done . 1 remaining" in output
    assert "[1] Continue building" in output
    assert "Reply with 1-7:" in output


def test_go_suggests_flow_command(tmp_path, capsys):
    result = cli.main(["--project-dir", str(tmp_path), "go", "add", "password", "reset"])

    assert result == 0
    output = capsys.readouterr().out
    assert "Pathly go" in output
    assert "pathly flow add-password-reset" in output


def test_flow_alias_uses_team_flow_root(tmp_path, monkeypatch):
    seen = {}

    class FakeDriver:
        def __init__(self, feature, mode, entry, runner):
            seen["feature"] = feature
            seen["mode"] = mode
            seen["entry"] = entry
            seen["runner"] = runner
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
        "runner": None,
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
    assert "pathly install codex --apply" in output
    assert "$plugin\\skills" in output
    assert '"path": "./plugins/pathly"' in output
    assert "codex plugin marketplace add" in output
    assert "globally on this machine" in output


def test_install_codex_apply_creates_marketplace(tmp_path, capsys, monkeypatch):
    def fake_link(path, target):
        path.mkdir()
        (path / ".target").write_text(str(target), encoding="utf-8")

    monkeypatch.setattr(codex_installer, "replace_link_or_empty_dir", fake_link)

    result = cli.main(["install", "codex", "--apply", "--market", str(tmp_path)])

    assert result == 0
    output = capsys.readouterr().out
    assert f"Installed Pathly Codex marketplace at {tmp_path.resolve()}" in output
    assert "Restart Codex" in output
    assert (tmp_path / ".agents" / "plugins" / "marketplace.json").exists()
    assert (tmp_path / "plugins" / "pathly" / ".codex-plugin" / ".target").exists()
    assert (tmp_path / "plugins" / "pathly" / "skills" / ".target").exists()
    assert (tmp_path / "plugins" / "pathly" / "core" / ".target").exists()


def test_run_uses_current_project_as_team_flow_root(tmp_path, monkeypatch):
    seen = {}

    class FakeDriver:
        def __init__(self, feature, mode, entry, runner):
            seen["feature"] = feature
            seen["mode"] = mode
            seen["entry"] = entry
            seen["runner"] = runner
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
        "runner": None,
        "root": Path(tmp_path).resolve(),
        "ran": True,
    }


def test_flow_passes_runner_selection_to_driver(tmp_path, monkeypatch):
    seen = {}

    class FakeDriver:
        def __init__(self, feature, mode, entry, runner):
            seen["feature"] = feature
            seen["mode"] = mode
            seen["entry"] = entry
            seen["runner"] = runner

        def run(self):
            seen["ran"] = True

    monkeypatch.setattr(team_flow, "Driver", FakeDriver)

    result = cli.main([
        "--project-dir", str(tmp_path), "flow", "checkout-flow", "--entry", "build", "--runner", "codex",
    ])

    assert result == 0
    assert seen == {
        "feature": "checkout-flow",
        "mode": "interactive",
        "entry": "build",
        "runner": "codex",
        "ran": True,
    }


def test_init_rejects_path_traversal_feature_name(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--project-dir", str(tmp_path), "init", "..\\escape"])

    assert exc_info.value.code != 0
    assert not (tmp_path.parent / "escape").exists()
    assert "no path segments" in capsys.readouterr().err


def test_flow_rejects_path_separator_before_driver_runs(tmp_path, monkeypatch, capsys):
    def fail_driver(*args, **kwargs):
        raise AssertionError("driver should not run for invalid feature names")

    monkeypatch.setattr(team_flow, "Driver", fail_driver)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--project-dir", str(tmp_path), "flow", "bad/name"])

    assert exc_info.value.code != 0
    assert "no path segments" in capsys.readouterr().err


def test_help_plan_menu_exposes_meet(tmp_path, capsys):
    cli.main(["--project-dir", str(tmp_path), "init", "checkout-flow"])
    progress = tmp_path / "plans" / "checkout-flow" / "PROGRESS.md"
    progress.write_text(
        "# Progress\n\n| Conversation | Status |\n|---|---|\n| 1 | DONE |\n| 2 | TODO |\n",
        encoding="utf-8",
    )
    capsys.readouterr()

    result = cli.main(["--project-dir", str(tmp_path), "help"])

    assert result == 0
    output = capsys.readouterr().out
    assert "[5] Meet a role" in output
    assert "Reply with 1-7:" in output


def test_meet_writes_consult_note(tmp_path, monkeypatch, capsys):
    cli.main(["--project-dir", str(tmp_path), "init", "checkout-flow"])

    def fake_run(prompt, *, cwd, allowed_tools, timeout=None):
        assert allowed_tools == constants.READ_ONLY_TOOLS
        assert cwd == Path(tmp_path).resolve()
        return """# Meet Note - planner - checkout-flow

## Question
What should conversation 2 verify?

## Answer
Verify the saved filter is restored on reload.

## Evidence
- plans/checkout-flow/PROGRESS.md

## Recommendation
Keep the verification in the second conversation.

## Promotion Target
planner"""

    monkeypatch.setattr(cli.manager.ClaudeTextAgent, "run", lambda self, *args, **kwargs: fake_run(*args, **kwargs))
    monkeypatch.setattr(meet_command.shutil, "which", lambda name: "claude" if name == "claude" else None)

    result = cli.main([
        "--project-dir", str(tmp_path), "meet", "checkout-flow",
        "--role", "planner",
        "--question", "What should conversation 2 verify?",
        "--next", "return",
    ])

    assert result == 0
    output = capsys.readouterr().out
    assert "Suggested promotion target: planner" in output
    consults = list((tmp_path / "plans" / "checkout-flow" / "consults").glob("*-planner.md"))
    assert len(consults) == 1
    assert "Verify the saved filter is restored on reload." in consults[0].read_text(encoding="utf-8")


def test_version_flag_prints_version_and_exits(capsys):
    result = cli.main(["--version"])

    assert result == 0
    output = capsys.readouterr().out
    assert output.startswith("pathly ")
    assert "2.0.0" in output


def test_version_short_flag_prints_version_and_exits(capsys):
    result = cli.main(["-V"])

    assert result == 0
    output = capsys.readouterr().out
    assert output.startswith("pathly ")
    assert "2.0.0" in output


def test_version_flag_works_as_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "pathly.cli", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.startswith("pathly ")
    assert "2.0.0" in result.stdout


def test_meet_planner_promotion_uses_plan_write_tools(tmp_path, monkeypatch, capsys):
    cli.main(["--project-dir", str(tmp_path), "init", "checkout-flow"])
    calls = []

    def fake_run(prompt, *, cwd, allowed_tools, timeout=None):
        calls.append(allowed_tools)
        if allowed_tools == constants.READ_ONLY_TOOLS:
            return """# Meet Note - architect - checkout-flow

## Question
Should this need architecture notes?

## Answer
Yes, because it changes a shared flow.

## Evidence
- plans/checkout-flow/IMPLEMENTATION_PLAN.md

## Recommendation
Add architecture notes before build resumes.

## Promotion Target
architect"""
        return "Updated ARCHITECTURE_PROPOSAL.md with shared-flow notes."

    monkeypatch.setattr(cli.manager.ClaudeTextAgent, "run", lambda self, *args, **kwargs: fake_run(*args, **kwargs))
    monkeypatch.setattr(meet_command.shutil, "which", lambda name: "claude" if name == "claude" else None)

    result = cli.main([
        "--project-dir", str(tmp_path), "meet", "checkout-flow",
        "--role", "architect",
        "--question", "Should this need architecture notes?",
        "--next", "architect",
    ])

    assert result == 0
    output = capsys.readouterr().out
    assert "Updated ARCHITECTURE_PROPOSAL.md with shared-flow notes." in output
    assert calls == [constants.READ_ONLY_TOOLS, constants.PLAN_WRITE_TOOLS]
