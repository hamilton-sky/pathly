"""Configuration objects for the candidate team-flow runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MAX_RETRIES = 2


@dataclass(frozen=True)
class DriverConfig:
    repo_root: Path
    feature: str
    mode: str
    entry: str

    @property
    def plan_dir(self) -> Path:
        return self.repo_root / "plans" / self.feature

    @property
    def feedback_dir(self) -> Path:
        return self.plan_dir / "feedback"

    @property
    def progress_file(self) -> Path:
        return self.plan_dir / "PROGRESS.md"
