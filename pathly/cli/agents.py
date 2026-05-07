"""Agent interfaces and concrete text-agent adapter for the candidate CLI."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Protocol


class TextAgent(Protocol):
    def run(
        self,
        prompt: str,
        *,
        cwd: Path,
        allowed_tools: str,
        timeout: int | None = None,
    ) -> str:
        """Run a text-only agent command and return stdout."""


class ClaudeTextAgent:
    def run(
        self,
        prompt: str,
        *,
        cwd: Path,
        allowed_tools: str,
        timeout: int | None = None,
    ) -> str:
        timeout = timeout or int(os.environ.get("CLAUDE_AGENT_TIMEOUT", "1800"))
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", allowed_tools],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "claude consultation failed").strip()
            raise RuntimeError(details)
        return result.stdout.strip()
