#!/bin/bash
# install.sh — Pathly installer for Claude Code
#
# Usage:
#   bash install.sh            # install
#   bash install.sh --uninstall  # remove
#
# What it installs:
#   adapters/claude-code/skills/ → ~/.claude/skills/   (slash commands)
#   adapters/claude-code/agents/ → ~/.claude/agents/   (sub-agents)
#   hooks/    → ~/.claude/plugins/pathly/hooks/
#
# After install, register the feedback hook (optional):
#   bash scripts/setup-hook.sh

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
PLUGIN_NAME="pathly"
LEGACY_PLUGIN_NAME="claude-agents-framework"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILL_SOURCE="$SCRIPT_DIR/adapters/claude-code/skills"
CLAUDE_AGENT_SOURCE="$SCRIPT_DIR/adapters/claude-code/agents"
UNINSTALL="${1:-}"

echo ""
echo "Pathly"
echo "======"
echo ""

if [ "$UNINSTALL" = "--uninstall" ]; then
    echo "Uninstalling..."
    for skill_dir in "$CLAUDE_SKILL_SOURCE"/*/; do
        skill_name=$(basename "$skill_dir")
        rm -rf "$CLAUDE_DIR/skills/$skill_name"
        echo "  - /$skill_name"
    done
    for agent_file in "$CLAUDE_AGENT_SOURCE"/*.md; do
        agent_name=$(basename "$agent_file")
        rm -f "$CLAUDE_DIR/agents/$agent_name"
        echo "  - $agent_name"
    done
    rm -rf "$CLAUDE_DIR/plugins/$PLUGIN_NAME"
    rm -rf "$CLAUDE_DIR/plugins/$LEGACY_PLUGIN_NAME"
    echo ""
    echo "Uninstalled. Run 'bash scripts/setup-hook.sh --remove' to remove the hook."
    echo "Note: skills and agents in ~/.claude/ must be removed manually if desired."
    echo ""
    exit 0
fi

# Skills
echo "Installing skills..."
mkdir -p "$CLAUDE_DIR/skills"
for skill_dir in "$CLAUDE_SKILL_SOURCE"/*/; do
    skill_name=$(basename "$skill_dir")
    cp -r "$skill_dir" "$CLAUDE_DIR/skills/$skill_name"
    echo "  + /$skill_name"
done

# Agents
echo ""
echo "Installing agents..."
mkdir -p "$CLAUDE_DIR/agents"
for agent_file in "$CLAUDE_AGENT_SOURCE"/*.md; do
    agent_name=$(basename "$agent_file")
    [ "$agent_name" = "README.md" ] && continue
    cp "$agent_file" "$CLAUDE_DIR/agents/$agent_name"
    echo "  + $agent_name"
done

# Templates
echo ""
echo "Installing templates..."
mkdir -p "$CLAUDE_DIR/plugins/$PLUGIN_NAME/templates"
cp -r "$SCRIPT_DIR/templates/"* "$CLAUDE_DIR/plugins/$PLUGIN_NAME/templates/"
echo "  + templates/plan/"

# Hooks runtime
echo ""
echo "Installing hooks..."
mkdir -p "$CLAUDE_DIR/plugins/$PLUGIN_NAME/hooks"
cp "$SCRIPT_DIR/hooks/"*.py "$CLAUDE_DIR/plugins/$PLUGIN_NAME/hooks/"
echo "  + classify_feedback.py"

echo ""
echo "Done. Installed to $CLAUDE_DIR"
echo ""
echo "Next step — register the feedback hook (optional):"
echo "  bash scripts/setup-hook.sh"
echo ""
