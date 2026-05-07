"""Filesystem and git helpers for the candidate team-flow runtime."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from orchestrator.feedback import open_feedback_files

from .config import DriverConfig


class TeamFlowFiles:
    def __init__(self, config: DriverConfig):
        self.config = config

    def feedback_files(self) -> set:
        return open_feedback_files(self.config.feedback_dir)

    def git_diff(self) -> str:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", ".", ":(exclude)plans/"],
            cwd=str(self.config.repo_root),
            capture_output=True,
            text=True,
        )
        return result.stdout

    def git_is_clean(self) -> bool:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(self.config.repo_root),
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() == ""

    def all_conversations_done(self) -> bool:
        if not self.config.progress_file.exists():
            return False
        return "| TODO |" not in self.config.progress_file.read_text(encoding="utf-8")

    def missing_core_plan_files(self) -> list[str]:
        required = [
            "USER_STORIES.md",
            "IMPLEMENTATION_PLAN.md",
            "PROGRESS.md",
            "CONVERSATION_PROMPTS.md",
        ]
        return [name for name in required if not (self.config.plan_dir / name).exists()]

    def event_ids(self, events_path: Path) -> set:
        ids = set()
        if not events_path.exists():
            return ids
        try:
            with open(events_path, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "id" in event:
                        ids.add(event["id"])
                    if "timestamp" in event:
                        ids.add(event["timestamp"])
        except OSError:
            return set()
        return ids

    def feedback_ttl_issue(self, feedback_file: Path, known_event_ids: set) -> str:
        try:
            content = feedback_file.read_text(encoding="utf-8")
        except OSError:
            return ""

        if not content.startswith("---"):
            return ""

        end = content.find("---", 3)
        if end == -1:
            return ""

        frontmatter = {}
        for line in content[3:end].splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                frontmatter[key.strip()] = value.strip()

        event_id = frontmatter.get("created_by_event", "")
        created_at = frontmatter.get("created_at", "")
        ttl_hours = frontmatter.get("ttl_hours", "24")

        if event_id and event_id != "unknown" and known_event_ids and event_id not in known_event_ids:
            return f"event {event_id} not in current EVENTS.jsonl (orphan from a previous run)"

        if created_at:
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                ttl = timedelta(hours=float(ttl_hours))
                if datetime.now(timezone.utc) > created + ttl:
                    return f"TTL expired (created {created_at}, ttl={ttl_hours}h)"
            except (TypeError, ValueError):
                return ""

        return ""
