#!/bin/bash
# setup-hook.sh — Register the classify_feedback hook in ~/.claude/settings.json
# This is the ONLY thing that touches ~/.claude/ after plugin install.
# Run once after installing the plugin.
#
# Usage: bash scripts/setup-hook.sh
#        bash scripts/setup-hook.sh --remove   (to unregister)

set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"
PLUGIN_DIR="$HOME/.claude/plugins/claude-agents-framework"
HOOK_CMD="python $PLUGIN_DIR/hooks/classify_feedback.py"

# Ensure settings.json exists
if [ ! -f "$SETTINGS" ]; then
  echo '{}' > "$SETTINGS"
fi

ACTION="${1:-}"

python3 - <<PYEOF
import json, sys

settings_file = "$SETTINGS"
hook_cmd = "$HOOK_CMD"
action = "$ACTION"

with open(settings_file) as f:
    try:
        settings = json.load(f)
    except json.JSONDecodeError:
        settings = {}

hooks = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])

def is_our_hook(h):
    return h.get("matcher") == "Write" and any(
        "classify_feedback.py" in hh.get("command", "")
        for hh in h.get("hooks", [])
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
    if any(is_our_hook(h) for h in hooks):
        print("Hook already registered in settings.json — skipped")
    else:
        hooks.append({
            "matcher": "Write",
            "hooks": [{"type": "command", "command": hook_cmd}]
        })
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        print("Hook registered in settings.json")
        print(f"Command: {hook_cmd}")
PYEOF
