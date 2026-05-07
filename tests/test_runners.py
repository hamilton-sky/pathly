"""Tests for Pathly runner implementations."""

from pathlib import Path
from types import SimpleNamespace

from pathly.runners import ALLOWED_TOOLS, ClaudeRunner, CodexRunner, RunnerResult


def test_runner_result_has_normalized_defaults():
    result = RunnerResult(return_code=0)

    assert result.return_code == 0
    assert result.usage == {}
    assert result.stdout == ""
    assert result.stderr == ""


def test_claude_runner_preserves_json_command_shape(capsys):
    calls = []
    repo_root = Path.cwd()

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout='{"model":"claude-test","usage":{"input_tokens":3,"output_tokens":5},"cost_usd":0.01}',
            stderr="",
        )

    runner = ClaudeRunner(repo_root=repo_root, run_command=fake_run)

    result = runner.run("do the work")

    assert result.return_code == 0
    assert result.usage == {
        "model": "claude-test",
        "tokens_in": 3,
        "tokens_out": 5,
        "cost_usd": 0.01,
    }
    assert calls[0][0] == [
        "claude",
        "-p",
        "do the work",
        "--allowedTools",
        ALLOWED_TOOLS,
        "--output-format",
        "json",
    ]
    assert calls[0][1]["cwd"] == str(repo_root)
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["text"] is True
    assert calls[0][1]["timeout"] == 1800
    assert capsys.readouterr().out == (
        '{"model":"claude-test","usage":{"input_tokens":3,"output_tokens":5},"cost_usd":0.01}'
    )


def test_codex_runner_constructs_exec_command(capsys):
    calls = []
    repo_root = Path.cwd()

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="done\n", stderr="")

    runner = CodexRunner(repo_root=repo_root, run_command=fake_run)

    result = runner.run("Use Pathly help")

    assert result.return_code == 0
    assert result.usage == {}
    assert calls[0][0] == ["codex", "exec", "-C", str(repo_root), "Use Pathly help"]
    assert calls[0][1]["cwd"] == str(repo_root)
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["text"] is True
    assert calls[0][1]["timeout"] == 1800
    assert capsys.readouterr().out == "done\n"
