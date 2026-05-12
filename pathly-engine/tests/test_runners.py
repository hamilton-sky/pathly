"""Tests for Pathly runner implementations."""

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from runners.base import RUNNER_TIMEOUT_ENV_VAR
from runners import ALLOWED_TOOLS, ClaudeRunner, CodexRunner, RunnerResult
from runners.claude import TIMEOUT_ENV_VAR


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


def test_claude_is_available_returns_false_on_timeout():
    def hanging_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 5))

    runner = ClaudeRunner(repo_root=Path.cwd(), run_command=hanging_run)

    assert runner.is_available() is False


def test_codex_is_available_returns_false_on_timeout():
    def hanging_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 5))

    runner = CodexRunner(repo_root=Path.cwd(), run_command=hanging_run)

    assert runner.is_available() is False


def test_claude_runner_clamps_low_timeout(monkeypatch, capsys):
    calls = []
    monkeypatch.setenv(TIMEOUT_ENV_VAR, "0")

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    runner = ClaudeRunner(repo_root=Path.cwd(), run_command=fake_run)

    result = runner.run("do the work")

    assert result.return_code == 0
    assert calls[0][1]["timeout"] == 60
    assert "below minimum" in capsys.readouterr().err


def test_claude_runner_clamps_high_timeout(monkeypatch, capsys):
    calls = []
    monkeypatch.setenv(TIMEOUT_ENV_VAR, "7201")

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    runner = ClaudeRunner(repo_root=Path.cwd(), run_command=fake_run)

    result = runner.run("do the work")

    assert result.return_code == 0
    assert calls[0][1]["timeout"] == 7200
    assert "exceeds maximum" in capsys.readouterr().err


def test_claude_runner_rejects_non_numeric_timeout(monkeypatch):
    monkeypatch.setenv(TIMEOUT_ENV_VAR, "never")
    runner = ClaudeRunner(repo_root=Path.cwd())

    with pytest.raises(ValueError, match="not a valid integer"):
        runner.run("do the work")


def test_codex_runner_clamps_timeout(monkeypatch, capsys):
    calls = []
    monkeypatch.setenv(RUNNER_TIMEOUT_ENV_VAR, "-1")

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    runner = CodexRunner(repo_root=Path.cwd(), run_command=fake_run)

    result = runner.run("do the work")

    assert result.return_code == 0
    assert calls[0][1]["timeout"] == 60
    assert "below minimum" in capsys.readouterr().err
