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
    assert "Reply with 1-6:" in output


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
    assert "pathly install codex --apply" in output
    assert "$plugin\\skills" in output
    assert '"path": "./plugins/pathly"' in output
    assert "codex plugin marketplace add" in output
    assert "globally on this machine" in output


def test_install_codex_apply_creates_marketplace(tmp_path, capsys, monkeypatch):
    def fake_link(path, target):
        path.mkdir()
        (path / ".target").write_text(str(target), encoding="utf-8")

    monkeypatch.setattr(cli, "_replace_link_or_empty_dir", fake_link)

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
