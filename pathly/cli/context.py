"""Project context value objects for the candidate CLI."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectContext:
    root: Path

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ProjectContext":
        return cls(Path(args.project_dir).expanduser().resolve())
