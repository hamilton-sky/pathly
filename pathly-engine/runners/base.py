"""Shared runner contract for Pathly workflow drivers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


DEFAULT_TIMEOUT_SECONDS = 1800
RUNNER_TIMEOUT_ENV_VAR = "PATHLY_RUNNER_TIMEOUT"


class RunnerError(RuntimeError):
    """Base error for runner setup and execution failures."""


class RunnerTimeoutError(RunnerError):
    """Raised when a runner exceeds its configured timeout."""


@dataclass(frozen=True)
class RunnerResult:
    return_code: int
    usage: dict = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""


class Runner(Protocol):
    name: str
    repo_root: Path

    def run(self, prompt: str) -> RunnerResult:
        """Run one agent prompt and return the normalized process result."""

    def is_available(self) -> bool:
        """Return whether the underlying CLI is available."""
