#!/usr/bin/env python3
"""Inject TTL frontmatter into Pathly feedback files after write events."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

from pathly.hooks.contracts import HookPayload, HookResult


FEEDBACK_FILES = {
    "ARCH_FEEDBACK.md",
    "REVIEW_FAILURES.md",
    "TEST_FAILURES.md",
    "IMPL_QUESTIONS.md",
    "DESIGN_QUESTIONS.md",
    "HUMAN_QUESTIONS.md",
}

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?---\s*\n", re.DOTALL)
TTL_HOURS = 24


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    handle(data)


def handle(data: HookPayload) -> HookResult:
    name = "inject_feedback_ttl"
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    basename = os.path.basename(file_path)
    if basename not in FEEDBACK_FILES:
        return HookResult(name=name)

    normalized = file_path.replace("\\", "/")
    if "/feedback/" not in normalized:
        return HookResult(name=name)

    if not os.path.exists(file_path):
        return HookResult(name=name)

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    if content.startswith("---"):
        return HookResult(name=name, handled=True)

    event_id = _last_event_id(file_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    frontmatter = (
        "---\n"
        f"created_at: {now}\n"
        f"created_by_event: {event_id}\n"
        f"ttl_hours: {TTL_HOURS}\n"
        "---\n\n"
    )

    _atomic_write(file_path, frontmatter + content)

    message = f"[inject_feedback_ttl] {basename} - frontmatter injected (ttl={TTL_HOURS}h, event={event_id})"
    print(message)
    return HookResult(name=name, handled=True, changed=True, message=message)


def _last_event_id(feedback_path: str) -> str:
    feedback_dir = os.path.dirname(feedback_path)
    feature_dir = os.path.dirname(feedback_dir)
    events_path = os.path.join(feature_dir, "EVENTS.jsonl")

    if not os.path.exists(events_path):
        return "unknown"

    last_id = "unknown"
    try:
        with open(events_path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    if "id" in evt:
                        last_id = evt["id"]
                    elif "timestamp" in evt:
                        last_id = evt["timestamp"]
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return last_id


def _atomic_write(file_path: str, text: str, encoding: str = "utf-8") -> None:
    dir_ = os.path.dirname(os.path.abspath(file_path))
    fd, tmp = tempfile.mkstemp(dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
        os.replace(tmp, file_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


if __name__ == "__main__":
    main()
