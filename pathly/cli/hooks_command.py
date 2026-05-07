"""CLI surface for portable Pathly hooks."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pathly.hooks import run_event
from pathly.hooks.contracts import HookEvent, validate_hook_payload


class HooksCommand:
    def run(self, args: argparse.Namespace) -> int:
        if args.hooks_action == "run":
            return self.run_event(args.event, args.payload)
        if args.hooks_action == "print-config":
            return self.print_config(args.host)
        if args.hooks_action == "install":
            return self.install(args.host)
        raise AssertionError(args.hooks_action)

    def run_event(self, event: str, payload_arg: str) -> int:
        try:
            hook_event = HookEvent(event)
        except ValueError:
            print(f"Unsupported hook event: {event}", file=sys.stderr)
            return 2

        try:
            payload = _read_payload(payload_arg)
        except json.JSONDecodeError as exc:
            print(f"Invalid hook payload JSON: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"Unable to read hook payload: {exc}", file=sys.stderr)
            return 2

        run_event(hook_event, payload)
        return 0

    def print_config(self, host: str) -> int:
        if host == "claude":
            print(json.dumps(claude_config(), indent=2))
            return 0

        print(json.dumps(unavailable_config(host), indent=2))
        return 0

    def install(self, host: str) -> int:
        if host != "claude":
            print(f"`pathly hooks install {host}` is not supported yet.", file=sys.stderr)
            return 2

        settings_path = _claude_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            settings = _read_json_object(settings_path)
        except json.JSONDecodeError as exc:
            print(f"Invalid Claude settings JSON in {settings_path}: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"Invalid Claude settings in {settings_path}: {exc}", file=sys.stderr)
            return 2

        hooks_config = settings.setdefault("hooks", {})
        if not isinstance(hooks_config, dict):
            print(f"Invalid Claude settings in {settings_path}: hooks must be a JSON object.", file=sys.stderr)
            return 2

        hooks = hooks_config.setdefault("PostToolUse", [])
        if not isinstance(hooks, list):
            print(f"Invalid Claude settings in {settings_path}: hooks.PostToolUse must be a JSON array.", file=sys.stderr)
            return 2

        config_hooks = claude_config()["hooks"]["PostToolUse"]

        def is_pathly_command(command: object) -> bool:
            if not isinstance(command, str):
                return False
            return (
                "pathly.hooks post-tool-use" in command
                or "classify_feedback.py" in command
                or "inject_feedback_ttl.py" in command
            )

        def without_pathly_hooks(entry: object) -> object | None:
            if not isinstance(entry, dict):
                return entry
            entry_hooks = entry.get("hooks", [])
            if not isinstance(entry_hooks, list):
                return entry
            remaining = [
                hook
                for hook in entry_hooks
                if not (isinstance(hook, dict) and is_pathly_command(hook.get("command")))
            ]
            if len(remaining) == len(entry_hooks):
                return entry
            if not remaining:
                return None
            updated = dict(entry)
            updated["hooks"] = remaining
            return updated

        hooks[:] = [
            updated
            for entry in hooks
            if (updated := without_pathly_hooks(entry)) is not None
        ]
        hooks.extend(config_hooks)
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        print(f"Installed Pathly Claude hooks in {settings_path}")
        return 0


def claude_config() -> dict[str, object]:
    return {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Write",
                    "hooks": [
                        {"type": "command", "command": f"{_module_command('pathly.hooks')} post-tool-use"},
                    ],
                }
            ]
        }
    }


def unavailable_config(host: str) -> dict[str, object]:
    return {
        "host": host,
        "native_hooks": "unavailable",
        "reason": "Pathly does not know a documented native hook schema for this host.",
        "runtime": "pathly hooks run post-tool-use --payload <fixture-json>",
    }


def _module_command(module: str) -> str:
    executable = Path(sys.executable).name if sys.executable else "python"
    if os.name == "nt":
        executable = "python"
    return f"{executable} -m {module}"


def _claude_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def _read_payload(payload_arg: str) -> dict[str, object]:
    if payload_arg == "-":
        return validate_hook_payload(json.load(sys.stdin))

    path = Path(payload_arg)
    if path.exists():
        return validate_hook_payload(json.loads(path.read_text(encoding="utf-8-sig")))

    return validate_hook_payload(json.loads(payload_arg))


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("settings file must be a JSON object.")
    return data
