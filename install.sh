#!/bin/bash
# install.sh — Pathly installer for Claude Code
#
# Usage:
#   bash install.sh            # install
#   bash install.sh --uninstall  # remove
#
# What it installs:
#   core/skills/ → ~/.claude/skills/   (slash commands)
#   adapters/claude/agents/ → ~/.claude/agents/   (sub-agents)
#
# After install, register the feedback hook (optional):
#   python -m pip install -e .
#   pathly hooks install claude

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
PLUGIN_NAME="pathly"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILL_SOURCE="$SCRIPT_DIR/core/skills"
CLAUDE_AGENT_SOURCE="$SCRIPT_DIR/adapters/claude/agents"
CORE_TEMPLATE_SOURCE="$SCRIPT_DIR/core/templates"
UNINSTALL="${1:-}"

echo ""
echo "Pathly"
echo "======"
echo ""

if [ "$UNINSTALL" = "--uninstall" ]; then
    echo "Uninstalling..."
    for skill_file in "$CLAUDE_SKILL_SOURCE"/*.md; do
        skill_name=$(basename "$skill_file" .md)
        rm -f "$CLAUDE_DIR/skills/$skill_name.md"
        echo "  - /$skill_name"
    done
    for agent_file in "$CLAUDE_AGENT_SOURCE"/*.md; do
        agent_name=$(basename "$agent_file")
        rm -f "$CLAUDE_DIR/agents/$agent_name"
        echo "  - $agent_name"
    done
    rm -rf "$CLAUDE_DIR/plugins/$PLUGIN_NAME"
    echo ""
    echo "Uninstalled. Remove Pathly entries from ~/.claude/settings.json if desired."
    echo "Note: skills and agents in ~/.claude/ must be removed manually if desired."
    echo ""
    exit 0
fi

# Skills
echo "Installing skills..."
mkdir -p "$CLAUDE_DIR/skills"
for skill_file in "$CLAUDE_SKILL_SOURCE"/*.md; do
    skill_name=$(basename "$skill_file" .md)
    cp "$skill_file" "$CLAUDE_DIR/skills/$skill_name.md"
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
cp -r "$CORE_TEMPLATE_SOURCE/"* "$CLAUDE_DIR/plugins/$PLUGIN_NAME/templates/"
echo "  + templates/plan/"

echo ""
echo "Done. Installed to $CLAUDE_DIR"
echo ""
echo "Next step — register the feedback hook (optional):"
echo "  python -m pip install -e ."
echo "  pathly hooks install claude"
echo ""
