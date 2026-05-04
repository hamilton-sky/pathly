#!/bin/bash
# install.sh — Claude Agents Framework installer
#
# Usage:
#   bash install.sh            # install
#   bash install.sh --uninstall  # remove
#
# What it installs:
#   skills/   → ~/.claude/skills/   (slash commands)
#   agents/   → ~/.claude/agents/   (sub-agents)
#   hooks/    → ~/.claude/plugins/claude-agents-framework/hooks/
#
# After install, register the feedback hook (optional):
#   bash scripts/setup-hook.sh

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNINSTALL="${1:-}"

echo ""
echo "Claude Agents Framework"
echo "======================="
echo ""

if [ "$UNINSTALL" = "--uninstall" ]; then
    echo "Uninstalling..."
    for skill_dir in "$SCRIPT_DIR/skills"/*/; do
        skill_name=$(basename "$skill_dir")
        rm -rf "$CLAUDE_DIR/skills/$skill_name"
        echo "  - /$skill_name"
    done
    for agent_file in "$SCRIPT_DIR/agents"/*.md; do
        agent_name=$(basename "$agent_file")
        rm -f "$CLAUDE_DIR/agents/$agent_name"
        echo "  - $agent_name"
    done
    rm -rf "$CLAUDE_DIR/plugins/claude-agents-framework"
    echo ""
    echo "Uninstalled. Run 'bash scripts/setup-hook.sh --remove' to remove the hook."
    echo "Note: skills and agents in ~/.claude/ must be removed manually if desired."
    echo ""
    exit 0
fi

# Skills
echo "Installing skills..."
mkdir -p "$CLAUDE_DIR/skills"
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
    skill_name=$(basename "$skill_dir")
    cp -r "$skill_dir" "$CLAUDE_DIR/skills/$skill_name"
    echo "  + /$skill_name"
done

# Agents
echo ""
echo "Installing agents..."
mkdir -p "$CLAUDE_DIR/agents"
for agent_file in "$SCRIPT_DIR/agents"/*.md; do
    agent_name=$(basename "$agent_file")
    [ "$agent_name" = "README.md" ] && continue
    cp "$agent_file" "$CLAUDE_DIR/agents/$agent_name"
    echo "  + $agent_name"
done

# Templates
echo ""
echo "Installing templates..."
mkdir -p "$CLAUDE_DIR/plugins/claude-agents-framework/templates"
cp -r "$SCRIPT_DIR/templates/"* "$CLAUDE_DIR/plugins/claude-agents-framework/templates/"
echo "  + templates/plan/"

# Hooks runtime
echo ""
echo "Installing hooks..."
mkdir -p "$CLAUDE_DIR/plugins/claude-agents-framework/hooks"
cp "$SCRIPT_DIR/hooks/"*.py "$CLAUDE_DIR/plugins/claude-agents-framework/hooks/"
echo "  + classify_feedback.py"

echo ""
echo "Done. Installed to $CLAUDE_DIR"
echo ""
echo "Next step — register the feedback hook (optional):"
echo "  bash scripts/setup-hook.sh"
echo ""
