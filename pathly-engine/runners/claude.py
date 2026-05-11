"""Claude CLI runner implementation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from .base import DEFAULT_TIMEOUT_SECONDS, RUNNER_TIMEOUT_ENV_VAR, RunnerResult


ALLOWED_TOOLS = "Edit,Write,Read,Glob,Grep,Bash,Skill,TodoWrite,WebSearch,WebFetch,Agent"
TIMEOUT_ENV_VAR = "CLAUDE_AGENT_TIMEOUT"


def parse_usage(stdout: str) -> dict:
    """Extract token and cost fields from claude JSON output."""
    if not stdout:
        return {}
    try:
        data = json.loads(stdout)
        usage = data.get("usage", {})
        return {
            "model": data.get("model", ""),
            "tokens_in": usage.get("input_tokens", 0),
            "tokens_out": usage.get("output_tokens", 0),
            "cost_usd": data.get("cost_usd", 0.0),
        }
    except (json.JSONDecodeError, AttributeError):
        return {}


class ClaudeRunner:
    """Run Claude agents and parse their usage payloads."""

    name = "claude"

    def __init__(
        self,
        repo_root: Path,
        log: Callable[[str], None] | None = None,
        on_timeout: Callable[[int], None] | None = None,
        allowed_tools: str = ALLOWED_TOOLS,
        run_command: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ):
        self.repo_root = Path(repo_root)
        self.log = log
        self.on_timeout = on_timeout
        self.allowed_tools = allowed_tools
        self.run_command = run_command

    def run(self, prompt: str) -> RunnerResult:
        timeout = int(
            os.environ.get(
                TIMEOUT_ENV_VAR,
                os.environ.get(RUNNER_TIMEOUT_ENV_VAR, str(DEFAULT_TIMEOUT_SECONDS)),
            )
        )
        if self.log:
            self.log(">>> Spawning claude agent...")
        try:
            result = self.run_command(
                [
                    "claude",
                    "-p",
                    prompt,
                    "--allowedTools",
                    self.allowed_tools,
                    "--output-format",
                    "json",
                ],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            if self.log:
                self.log(f"[ERROR] Agent timed out after {timeout}s.")
            if self.on_timeout:
                self.on_timeout(timeout)
            return RunnerResult(return_code=1)

        usage = parse_usage(result.stdout)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return RunnerResult(
            return_code=result.returncode,
            usage=usage,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def is_available(self) -> bool:
        try:
            self.run_command(["claude", "--version"], capture_output=True, check=True, timeout=5)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
        return True
