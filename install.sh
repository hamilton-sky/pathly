#!/usr/bin/env bash
# Claude Agents Framework — installer
# Copies agents, skills, and templates into ~/.claude/
# Safe: backs up any existing files before overwriting.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
DATA_DIR="$REPO_DIR/claude_agents/data"
ORCH_DIR="$REPO_DIR/claude_agents/orchestrator"
BACKUP_DIR="$CLAUDE_DIR/.backup-$(date +%Y%m%d-%H%M%S)"

echo "Claude Agents Framework — Install"
echo "==================================="
echo "Source : $REPO_DIR"
echo "Target : $CLAUDE_DIR"
echo ""

# Backup existing files if they exist
if [ -d "$CLAUDE_DIR/agents" ] || [ -d "$CLAUDE_DIR/skills" ]; then
  echo "Backing up existing files to $BACKUP_DIR ..."
  mkdir -p "$BACKUP_DIR"
  [ -d "$CLAUDE_DIR/agents" ]    && cp -r "$CLAUDE_DIR/agents"    "$BACKUP_DIR/"
  [ -d "$CLAUDE_DIR/skills" ]    && cp -r "$CLAUDE_DIR/skills"    "$BACKUP_DIR/"
  [ -d "$CLAUDE_DIR/templates" ] && cp -r "$CLAUDE_DIR/templates" "$BACKUP_DIR/"
  echo "Backup done."
  echo ""
fi

# Create target directories
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$CLAUDE_DIR/templates/plan"
mkdir -p "$CLAUDE_DIR/hooks"
mkdir -p "$CLAUDE_DIR/orchestrator"

# Install agents
echo "Installing agents..."
cp -v "$DATA_DIR/agents/"*.md "$CLAUDE_DIR/agents/"

# Install skills (merge — don't wipe existing skills the user may have)
echo ""
echo "Installing skills..."
for skill_dir in "$DATA_DIR/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  mkdir -p "$CLAUDE_DIR/skills/$skill_name"
  cp -v "$skill_dir/SKILL.md" "$CLAUDE_DIR/skills/$skill_name/SKILL.md"
done

# Install templates
echo ""
echo "Installing plan templates..."
cp -v "$DATA_DIR/templates/plan/"*.md "$CLAUDE_DIR/templates/plan/"

# Install docs (optional — informational only)
echo ""
echo "Installing docs..."
cp -v "$DATA_DIR/docs/"*.md "$CLAUDE_DIR/"

# Install hooks
echo ""
echo "Installing hooks..."
cp -v "$DATA_DIR/hooks/classify_feedback.py" "$CLAUDE_DIR/hooks/"

# Install orchestrator FSM runtime
echo ""
echo "Installing orchestrator FSM..."
for f in "$ORCH_DIR/"*.py; do
  fname=$(basename "$f")
  [ "$fname" = "test_fsm.py" ] && continue
  cp -v "$f" "$CLAUDE_DIR/orchestrator/"
done

# Merge hook config into settings.json
echo ""
echo "Configuring settings.json..."
python3 - <<'PYEOF'
import json, os

settings_file = os.path.expanduser("~/.claude/settings.json")
hook_entry = {
    "matcher": "Write",
    "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/classify_feedback.py"}]
}

if os.path.exists(settings_file):
    with open(settings_file) as f:
        settings = json.load(f)
else:
    settings = {}

settings.setdefault("hooks", {}).setdefault("PostToolUse", [])
existing = settings["hooks"]["PostToolUse"]
already = any(
    h.get("matcher") == "Write" and
    any("classify_feedback.py" in hh.get("command", "") for hh in h.get("hooks", []))
    for h in existing
)
if not already:
    existing.append(hook_entry)
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)
    print("  Hook config added to settings.json")
else:
    print("  Hook config already present in settings.json — skipped")
PYEOF

echo ""
echo "==================================="
echo "Install complete."
echo ""
echo "Agents installed    : $(ls "$CLAUDE_DIR/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Skills installed    : $(ls -d "$CLAUDE_DIR/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "Templates installed : $(ls "$CLAUDE_DIR/templates/plan/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Hooks installed     : $(ls "$CLAUDE_DIR/hooks/"*.py 2>/dev/null | wc -l | tr -d ' ')"
echo "Orchestrator files  : $(ls "$CLAUDE_DIR/orchestrator/"*.py 2>/dev/null | wc -l | tr -d ' ')"
echo ""
echo "Start a new Claude Code session in any project and run:"
echo "  /go <what you want to build> — natural language entry point (recommended)"
echo ""
echo "Or use skills directly:"
echo "  /team-flow <feature-name>    — full pipeline with feedback loops"
echo "  /storm                       — brainstorm a feature"
echo "  /plan <feature-name>         — plan a feature"
