"""Logging helpers for the candidate team-flow runtime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class DriverLogger:
    def __init__(self, repo_root: Path, feature: str):
        logs = repo_root / "logs"
        logs.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = logs / f"team-flow-{feature}-{timestamp}.log"

    def log(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def banner(self, message: str) -> None:
        rule = "=" * 46
        self.log(rule)
        self.log(f"  {message}")
        self.log(rule)
