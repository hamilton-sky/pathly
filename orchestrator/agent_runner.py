"""Compatibility bridge for the Claude runner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pathly.runners.claude import ALLOWED_TOOLS, TIMEOUT_ENV_VAR, ClaudeRunner, parse_usage
from pathly.runners.base import DEFAULT_TIMEOUT_SECONDS


class AgentRunner:
    """Run Claude agents and return the legacy ``(returncode, usage)`` tuple."""

    def __init__(
        self,
        repo_root: Path,
        log: Callable[[str], None] | None = None,
        on_timeout: Callable[[int], None] | None = None,
        allowed_tools: str = ALLOWED_TOOLS,
        run_command: Callable | None = None,
    ):
        self.runner = ClaudeRunner(
            repo_root=Path(repo_root),
            log=log,
            on_timeout=on_timeout,
            allowed_tools=allowed_tools,
            **({"run_command": run_command} if run_command else {}),
        )

    def run(self, prompt: str) -> tuple[int, dict]:
        """Run claude agent. Returns (returncode, usage) where usage may be empty."""
        result = self.runner.run(prompt)
        return result.return_code, result.usage
