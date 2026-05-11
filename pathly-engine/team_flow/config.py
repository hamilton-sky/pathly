"""Configuration objects for the candidate team-flow runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestrator.constants import MAX_RETRIES

__all__ = ["MAX_RETRIES", "DriverConfig"]


@dataclass(frozen=True)
class DriverConfig:
    repo_root: Path
    feature: str
    mode: str
    entry: str

    def __post_init__(self) -> None:
        if not self.feature:
            raise ValueError("Feature name cannot be empty.")
        if any(c in self.feature for c in ("..", "/", "\\")):
            raise ValueError(f"Unsafe feature name: {self.feature!r}")

    @property
    def plan_dir(self) -> Path:
        return self.repo_root / "plans" / self.feature

    @property
    def feedback_dir(self) -> Path:
        return self.plan_dir / "feedback"

    @property
    def progress_file(self) -> Path:
        return self.plan_dir / "PROGRESS.md"
