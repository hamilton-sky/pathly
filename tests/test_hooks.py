"""Tests for portable hook execution and host config rendering."""

import json

from pathly import cli
from pathly.cli import hooks_command


def test_hooks_run_post_tool_use_injects_feedback_ttl(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    plan_dir = tmp_path / "plans" / "checkout-flow"
    feedback_dir = plan_dir / "feedback"
    feedback_dir.mkdir(parents=True)
    (plan_dir / "EVENTS.jsonl").write_text('{"id":"evt-123"}\n', encoding="utf-8")
    feedback_file = feedback_dir / "IMPL_QUESTIONS.md"
    feedback_file.write_text("# Questions\n\n- What should happen?\n", encoding="utf-8")
    payload = tmp_path / "payload.json"
    payload.write_text(
        json.dumps(
            {
                "tool_input": {
                    "file_path": str(feedback_file),
                    "content": feedback_file.read_text(encoding="utf-8"),
                }
            }
        ),
        encoding="utf-8",
    )

    result = cli.main(["hooks", "run", "post-tool-use", "--payload", str(payload)])

    assert result == 0
    output = capsys.readouterr().out
    content = feedback_file.read_text(encoding="utf-8")
    assert "[inject_feedback_ttl]" in output
    assert content.startswith("---\n")
    assert "created_by_event: evt-123" in content
    assert "ttl_hours: 24" in content


def test_hooks_run_rejects_non_object_payload_without_traceback(capsys):
    result = cli.main(["hooks", "run", "post-tool-use", "--payload", "[]"])

    captured = capsys.readouterr()
    assert result == 2
    assert "Invalid hook payload: expected a JSON object." in captured.err
    assert "Traceback" not in captured.err


def test_hooks_print_config_claude_uses_python_runtime(capsys):
    result = cli.main(["hooks", "print-config", "claude"])

    assert result == 0
    config = json.loads(capsys.readouterr().out)
    hooks = config["hooks"]["PostToolUse"][0]["hooks"]
    assert hooks == [
        {
            "type": "command",
            "command": "python -m pathly.hooks post-tool-use",
        }
    ]


def test_hooks_print_config_marks_codex_and_cloud_unavailable(capsys):
    assert cli.main(["hooks", "print-config", "codex"]) == 0
    codex = json.loads(capsys.readouterr().out)
    assert codex["native_hooks"] == "unavailable"
    assert "documented native hook schema" in codex["reason"]

    assert cli.main(["hooks", "print-config", "cloud"]) == 0
    cloud = json.loads(capsys.readouterr().out)
    assert cloud["native_hooks"] == "unavailable"


def test_hooks_install_claude_writes_generated_config(tmp_path, capsys, monkeypatch):
    settings_path = tmp_path / ".claude" / "settings.json"
    monkeypatch.setattr(hooks_command, "_claude_settings_path", lambda: settings_path)

    result = cli.main(["hooks", "install", "claude"])

    assert result == 0
    output = capsys.readouterr().out
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert f"Installed Pathly Claude hooks in {settings_path}" in output
    assert settings["hooks"]["PostToolUse"] == hooks_command.claude_config()["hooks"]["PostToolUse"]


def test_hooks_install_claude_removes_stale_pathly_hooks_and_preserves_unrelated(tmp_path, monkeypatch):
    settings_path = tmp_path / ".claude" / "settings.json"
    monkeypatch.setattr(hooks_command, "_claude_settings_path", lambda: settings_path)
    settings_path.parent.mkdir(parents=True)
    unrelated_hook = {"type": "command", "command": "python custom_hook.py"}
    settings_path.write_text(
        json.dumps(
            {
                "permissions": {"allow": ["Read"]},
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python ~/.claude/plugins/pathly/" + "ho" + "oks/classify_feedback.py",
                                },
                                unrelated_hook,
                            ],
                        },
                        {
                            "matcher": "Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python ~/.claude/plugins/pathly/" + "ho" + "oks/inject_feedback_ttl.py",
                                }
                            ],
                        },
                        {
                            "matcher": "Write",
                            "hooks": [{"type": "command", "command": "python -m pathly.hooks post-tool-use"}],
                        },
                    ],
                    "PreToolUse": [{"matcher": "Read", "hooks": [unrelated_hook]}],
                },
            }
        ),
        encoding="utf-8",
    )

    result = cli.main(["hooks", "install", "claude"])

    assert result == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["permissions"] == {"allow": ["Read"]}
    assert settings["hooks"]["PreToolUse"] == [{"matcher": "Read", "hooks": [unrelated_hook]}]
    post_tool_use = settings["hooks"]["PostToolUse"]
    assert post_tool_use == [
        {"matcher": "Write", "hooks": [unrelated_hook]},
        *hooks_command.claude_config()["hooks"]["PostToolUse"],
    ]


def test_hooks_install_claude_preserves_invalid_settings_json(tmp_path, capsys, monkeypatch):
    settings_path = tmp_path / ".claude" / "settings.json"
    monkeypatch.setattr(hooks_command, "_claude_settings_path", lambda: settings_path)
    settings_path.parent.mkdir(parents=True)
    original = "{ invalid"
    settings_path.write_text(original, encoding="utf-8")

    result = cli.main(["hooks", "install", "claude"])

    captured = capsys.readouterr()
    assert result == 2
    assert "Invalid Claude settings JSON" in captured.err
    assert settings_path.read_text(encoding="utf-8") == original


def test_hooks_install_claude_preserves_non_object_settings_json(tmp_path, capsys, monkeypatch):
    settings_path = tmp_path / ".claude" / "settings.json"
    monkeypatch.setattr(hooks_command, "_claude_settings_path", lambda: settings_path)
    settings_path.parent.mkdir(parents=True)
    original = "[]"
    settings_path.write_text(original, encoding="utf-8")

    result = cli.main(["hooks", "install", "claude"])

    captured = capsys.readouterr()
    assert result == 2
    assert "settings file must be a JSON object" in captured.err
    assert settings_path.read_text(encoding="utf-8") == original


def test_hooks_install_claude_preserves_wrong_shape_hooks(tmp_path, capsys, monkeypatch):
    settings_path = tmp_path / ".claude" / "settings.json"
    monkeypatch.setattr(hooks_command, "_claude_settings_path", lambda: settings_path)
    settings_path.parent.mkdir(parents=True)
    original = '{"hooks":[]}'
    settings_path.write_text(original, encoding="utf-8")

    result = cli.main(["hooks", "install", "claude"])

    captured = capsys.readouterr()
    assert result == 2
    assert "hooks must be a JSON object" in captured.err
    assert settings_path.read_text(encoding="utf-8") == original


def test_hooks_install_claude_preserves_wrong_shape_post_tool_use(tmp_path, capsys, monkeypatch):
    settings_path = tmp_path / ".claude" / "settings.json"
    monkeypatch.setattr(hooks_command, "_claude_settings_path", lambda: settings_path)
    settings_path.parent.mkdir(parents=True)
    original = '{"hooks":{"PostToolUse":{}}}'
    settings_path.write_text(original, encoding="utf-8")

    result = cli.main(["hooks", "install", "claude"])

    captured = capsys.readouterr()
    assert result == 2
    assert "hooks.PostToolUse must be a JSON array" in captured.err
    assert settings_path.read_text(encoding="utf-8") == original
