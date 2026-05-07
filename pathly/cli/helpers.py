"""Small pure helpers for the candidate CLI."""

from __future__ import annotations

import argparse

from .constants import FEATURE_NAME_RE


def validate_feature_name(value: str) -> str:
    if not FEATURE_NAME_RE.fullmatch(value) or ".." in value:
        raise argparse.ArgumentTypeError(
            "feature must be 1-80 chars: letters, numbers, dots, underscores, or hyphens; no path segments"
        )
    return value


def feature_slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    parts = [part for part in slug.split("-") if part]
    return "-".join(parts[:6]) or "demo"


def prompt_choice(prompt: str, options: list[str]) -> str:
    print(prompt)
    while True:
        answer = input().strip().lower()
        if answer in options:
            return answer
        print(f"Reply with one of: {', '.join(options)}")


def return_route_for_state(feature: str, state: str) -> str:
    if state == "testing":
        return f"team-flow {feature} test"
    if state in {"review feedback open", "architecture feedback open"}:
        return f"team-flow {feature} build"
    if state == "done / retro complete":
        return f"help {feature}"
    return f"team-flow {feature} build"
