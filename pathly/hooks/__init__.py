"""Portable Pathly hook runtime."""

from __future__ import annotations

import json
import sys

from .classify_feedback import handle as classify_feedback
from .contracts import HookEvent, HookPayload, HookResult, validate_hook_payload
from .inject_feedback_ttl import handle as inject_feedback_ttl


def run_event(event: HookEvent | str, payload: HookPayload) -> list[HookResult]:
    hook_event = HookEvent(event)
    if hook_event is HookEvent.POST_TOOL_USE:
        return [
            inject_feedback_ttl(payload),
            classify_feedback(payload),
        ]
    raise ValueError(f"Unsupported hook event: {event}")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python -m pathly.hooks post-tool-use", file=sys.stderr)
        return 2
    try:
        payload = validate_hook_payload(json.load(sys.stdin))
        run_event(args[0], payload)
    except (json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


__all__ = ["HookEvent", "HookPayload", "HookResult", "main", "run_event"]
