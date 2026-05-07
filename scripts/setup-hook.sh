#!/bin/bash
# setup-hook.sh — Register Pathly feedback hooks in ~/.claude/settings.json
# This is the ONLY thing that touches ~/.claude/ after plugin install.
# Run once after installing the plugin.
#
# Usage: bash scripts/setup-hook.sh
#        bash scripts/setup-hook.sh --remove   (to unregister)

set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"
PLUGIN_DIR="$HOME/.claude/plugins/pathly"
CLASSIFY_HOOK_CMD="python $PLUGIN_DIR/hooks/classify_feedback.py"
TTL_HOOK_CMD="python $PLUGIN_DIR/hooks/inject_feedback_ttl.py"

# Ensure settings.json exists
mkdir -p "$(dirname "$SETTINGS")"
if [ ! -f "$SETTINGS" ]; then
  echo '{}' > "$SETTINGS"
fi

ACTION="${1:-}"

python3 - <<PYEOF
import json, sys

settings_file = "$SETTINGS"
hook_cmds = [
    "$CLASSIFY_HOOK_CMD",
    "$TTL_HOOK_CMD",
]
action = "$ACTION"

with open(settings_file) as f:
    try:
        settings = json.load(f)
    except json.JSONDecodeError:
        settings = {}

hooks = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])

def hook_command(h):
    commands = [
        hh.get("command", "")
        for hh in h.get("hooks", [])
    ]
    return commands[0] if commands else ""

def is_our_hook(h):
    return h.get("matcher") == "Write" and any(
        script in hook_command(h)
        for script in ("classify_feedback.py", "inject_feedback_ttl.py")
    )

if action == "--remove":
    before = len(hooks)
    settings["hooks"]["PostToolUse"] = [h for h in hooks if not is_our_hook(h)]
    after = len(settings["hooks"]["PostToolUse"])
    if before != after:
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        print("Hook removed from settings.json")
    else:
        print("Hook was not registered — nothing to remove")
else:
    existing = {hook_command(h) for h in hooks if h.get("matcher") == "Write"}
    added = []
    for hook_cmd in hook_cmds:
        if hook_cmd in existing:
            continue
        hooks.append({
            "matcher": "Write",
            "hooks": [{"type": "command", "command": hook_cmd}]
        })
        added.append(hook_cmd)
    if added:
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        print("Hooks registered in settings.json")
        for hook_cmd in added:
            print(f"Command: {hook_cmd}")
    else:
        print("Hooks already registered in settings.json — skipped")
PYEOF
