"""Tests for the Pathly agent subprocess runner."""

import subprocess
from pathlib import Path
from types import SimpleNamespace

from orchestrator.agent_runner import ALLOWED_TOOLS, AgentRunner, parse_usage


def test_parse_usage_extracts_expected_fields():
    stdout = (
        '{"model":"claude-test","usage":{"input_tokens":12,'
        '"output_tokens":34},"cost_usd":0.056}'
    )

    assert parse_usage(stdout) == {
        "model": "claude-test",
        "tokens_in": 12,
        "tokens_out": 34,
        "cost_usd": 0.056,
    }


def test_parse_usage_returns_empty_for_non_json_output():
    assert parse_usage("plain text output") == {}


def test_agent_runner_uses_claude_json_command(capsys):
    calls = []
    repo_root = Path.cwd()

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout='{"usage":{"input_tokens":1,"output_tokens":2}}',
            stderr="",
        )

    runner = AgentRunner(repo_root=repo_root, run_command=fake_run)

    returncode, usage = runner.run("do the work")

    assert returncode == 0
    assert usage["tokens_in"] == 1
    assert usage["tokens_out"] == 2
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
    assert capsys.readouterr().out == '{"usage":{"input_tokens":1,"output_tokens":2}}'


def test_agent_runner_timeout_returns_failure_and_notifies(monkeypatch):
    timeouts = []
    logs = []
    repo_root = Path.cwd()
    monkeypatch.setenv("CLAUDE_AGENT_TIMEOUT", "7")

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=kwargs.get("args", "claude"), timeout=7)

    runner = AgentRunner(
        repo_root=repo_root,
        log=logs.append,
        on_timeout=timeouts.append,
        run_command=fake_run,
    )

    assert runner.run("slow work") == (1, {})
    assert timeouts == [7]
    assert logs == [
        ">>> Spawning claude agent...",
        "[ERROR] Agent timed out after 7s.",
    ]
