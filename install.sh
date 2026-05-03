#!/usr/bin/env bash
# Claude Agents Framework — installer
# Copies agents, skills, and templates into ~/.claude/
# Safe: backs up any existing files before overwriting.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
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
  [ -d "$CLAUDE_DIR/agents" ] && cp -r "$CLAUDE_DIR/agents" "$BACKUP_DIR/"
  [ -d "$CLAUDE_DIR/skills" ] && cp -r "$CLAUDE_DIR/skills" "$BACKUP_DIR/"
  [ -d "$CLAUDE_DIR/templates" ] && cp -r "$CLAUDE_DIR/templates" "$BACKUP_DIR/"
  echo "Backup done."
  echo ""
fi

# Create target directories
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$CLAUDE_DIR/templates/plan"

# Install agents
echo "Installing agents..."
cp -v "$REPO_DIR/agents/"*.md "$CLAUDE_DIR/agents/"

# Install skills (merge — don't wipe existing skills the user may have)
echo ""
echo "Installing skills..."
for skill_dir in "$REPO_DIR/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  mkdir -p "$CLAUDE_DIR/skills/$skill_name"
  cp -v "$skill_dir/SKILL.md" "$CLAUDE_DIR/skills/$skill_name/SKILL.md"
done

# Install templates
echo ""
echo "Installing plan templates..."
cp -v "$REPO_DIR/templates/plan/"*.md "$CLAUDE_DIR/templates/plan/"

# Install docs (optional — informational only)
echo ""
echo "Installing docs..."
cp -v "$REPO_DIR/docs/"*.md "$CLAUDE_DIR/"

echo ""
echo "==================================="
echo "Install complete."
echo ""
echo "Agents installed  : $(ls "$CLAUDE_DIR/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Skills installed  : $(ls -d "$CLAUDE_DIR/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "Templates installed: $(ls "$CLAUDE_DIR/templates/plan/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo ""
echo "Start a new Claude Code session in any project and run:"
echo "  /team-flow <feature-name>   — full pipeline with feedback loops"
echo "  /storm                      — brainstorm a feature"
echo "  /plan <feature-name>        — plan a feature"
