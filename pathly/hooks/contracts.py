"""Shared contracts for portable hook execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class HookEvent(StrEnum):
    POST_TOOL_USE = "post-tool-use"


HookPayload = dict[str, Any]


@dataclass(frozen=True)
class HookResult:
    name: str
    handled: bool = False
    message: str = ""
    changed: bool = False


def validate_hook_payload(payload: object) -> HookPayload:
    if not isinstance(payload, dict):
        raise ValueError("Invalid hook payload: expected a JSON object.")
    tool_input = payload.get("tool_input")
    if tool_input is not None and not isinstance(tool_input, dict):
        raise ValueError("Invalid hook payload: tool_input must be an object when provided.")
    return payload
