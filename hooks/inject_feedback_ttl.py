#!/usr/bin/env python3
"""
inject_feedback_ttl.py — Claude Agents Framework hook

Fires after any Write tool call (PostToolUse).
If the written file is a feedback file inside plans/*/feedback/,
injects a YAML frontmatter block at the top (if not already present).

Frontmatter written:
  ---
  created_at: <ISO-8601 UTC timestamp>
  created_by_event: <last event id from EVENTS.jsonl, or "unknown">
  ttl_hours: 24
  ---

This makes "file exists = open issue" verifiable:
  - created_by_event not in EVENTS.jsonl → orphan from a previous run
  - created_at + ttl_hours elapsed              → stale, safe to prune
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

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


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    basename = os.path.basename(file_path)
    if basename not in FEEDBACK_FILES:
        return

    # Must be inside plans/*/feedback/
    normalized = file_path.replace("\\", "/")
    if "/feedback/" not in normalized:
        return

    if not os.path.exists(file_path):
        return

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Already has frontmatter — leave it alone
    if content.startswith("---"):
        return

    event_id = _last_event_id(file_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    frontmatter = (
        "---\n"
        f"created_at: {now}\n"
        f"created_by_event: {event_id}\n"
        f"ttl_hours: {TTL_HOURS}\n"
        "---\n\n"
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)

    print(f"[inject_feedback_ttl] {basename} — frontmatter injected (ttl={TTL_HOURS}h, event={event_id})")


def _last_event_id(feedback_path: str) -> str:
    """Return the id of the last event in EVENTS.jsonl, or 'unknown'."""
    # Walk up from feedback/ to find EVENTS.jsonl
    feedback_dir = os.path.dirname(feedback_path)
    feature_dir = os.path.dirname(feedback_dir)
    events_path = os.path.join(feature_dir, "EVENTS.jsonl")

    if not os.path.exists(events_path):
        return "unknown"

    last_id = "unknown"
    try:
        with open(events_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    if "id" in evt:
                        last_id = evt["id"]
                    elif "timestamp" in evt:
                        # Fall back to timestamp as ID if no explicit id field
                        last_id = evt["timestamp"]
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return last_id


if __name__ == "__main__":
    main()
