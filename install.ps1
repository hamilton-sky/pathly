# Claude Agents Framework — Windows installer
# Copies agents, skills, and templates into ~/.claude/
# Safe: backs up any existing files before overwriting.

$RepoDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir  = "$RepoDir\claude_agents\data"
$OrchDir  = "$RepoDir\claude_agents\orchestrator"
$ClaudeDir = "$env:USERPROFILE\.claude"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = "$ClaudeDir\.backup-$Timestamp"

Write-Host "Claude Agents Framework — Install"
Write-Host "==================================="
Write-Host "Source : $RepoDir"
Write-Host "Target : $ClaudeDir"
Write-Host ""

# Backup existing files
if ((Test-Path "$ClaudeDir\agents") -or (Test-Path "$ClaudeDir\skills")) {
    Write-Host "Backing up existing files to $BackupDir ..."
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    if (Test-Path "$ClaudeDir\agents")    { Copy-Item "$ClaudeDir\agents"    $BackupDir -Recurse }
    if (Test-Path "$ClaudeDir\skills")    { Copy-Item "$ClaudeDir\skills"    $BackupDir -Recurse }
    if (Test-Path "$ClaudeDir\templates") { Copy-Item "$ClaudeDir\templates" $BackupDir -Recurse }
    Write-Host "Backup done."
    Write-Host ""
}

# Create target directories
New-Item -ItemType Directory -Path "$ClaudeDir\agents"        -Force | Out-Null
New-Item -ItemType Directory -Path "$ClaudeDir\templates\plan" -Force | Out-Null
New-Item -ItemType Directory -Path "$ClaudeDir\hooks"          -Force | Out-Null
New-Item -ItemType Directory -Path "$ClaudeDir\orchestrator"   -Force | Out-Null

# Install agents
Write-Host "Installing agents..."
Copy-Item "$DataDir\agents\*.md" "$ClaudeDir\agents\" -Force -Verbose

# Install skills (merge)
Write-Host ""
Write-Host "Installing skills..."
Get-ChildItem "$DataDir\skills" -Directory | ForEach-Object {
    $skillName = $_.Name
    New-Item -ItemType Directory -Path "$ClaudeDir\skills\$skillName" -Force | Out-Null
    Copy-Item "$($_.FullName)\SKILL.md" "$ClaudeDir\skills\$skillName\SKILL.md" -Force -Verbose
}

# Install templates
Write-Host ""
Write-Host "Installing plan templates..."
Copy-Item "$DataDir\templates\plan\*.md" "$ClaudeDir\templates\plan\" -Force -Verbose

# Install docs
Write-Host ""
Write-Host "Installing docs..."
Copy-Item "$DataDir\docs\*.md" "$ClaudeDir\" -Force -Verbose

# Install hooks
Write-Host ""
Write-Host "Installing hooks..."
Copy-Item "$DataDir\hooks\classify_feedback.py" "$ClaudeDir\hooks\" -Force -Verbose

# Install orchestrator FSM runtime
Write-Host ""
Write-Host "Installing orchestrator FSM..."
Get-ChildItem "$OrchDir\*.py" | Where-Object { $_.Name -ne "test_fsm.py" } | ForEach-Object {
    Copy-Item $_.FullName "$ClaudeDir\orchestrator\" -Force -Verbose
}

# Merge hook config into settings.json
Write-Host ""
Write-Host "Configuring settings.json..."
$PythonScript = @'
import json, os

settings_file = os.path.join(os.environ["USERPROFILE"], ".claude", "settings.json")
hook_cmd = "python ~/.claude/hooks/classify_feedback.py"
hook_entry = {
    "matcher": "Write",
    "hooks": [{"type": "command", "command": hook_cmd}]
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
    print("  Hook config already present in settings.json -- skipped")
'@
python $PythonScript

Write-Host ""
Write-Host "==================================="
Write-Host "Install complete."
Write-Host ""
$agentCount = (Get-ChildItem "$ClaudeDir\agents\*.md"          -ErrorAction SilentlyContinue).Count
$skillCount  = (Get-ChildItem "$ClaudeDir\skills"    -Directory -ErrorAction SilentlyContinue).Count
$tmplCount   = (Get-ChildItem "$ClaudeDir\templates\plan\*.md" -ErrorAction SilentlyContinue).Count
$hookCount   = (Get-ChildItem "$ClaudeDir\hooks\*.py"          -ErrorAction SilentlyContinue).Count
$orchCount   = (Get-ChildItem "$ClaudeDir\orchestrator\*.py"   -ErrorAction SilentlyContinue).Count
Write-Host "Agents installed    : $agentCount"
Write-Host "Skills installed    : $skillCount"
Write-Host "Templates installed : $tmplCount"
Write-Host "Hooks installed     : $hookCount"
Write-Host "Orchestrator files  : $orchCount"
Write-Host ""
Write-Host "Start a new Claude Code session in any project and run:"
Write-Host "  /go <what you want to build>  -- natural language entry point (recommended)"
Write-Host ""
Write-Host "Or use skills directly:"
Write-Host "  /team-flow <feature-name>     -- full pipeline with feedback loops"
Write-Host "  /storm                        -- brainstorm a feature"
Write-Host "  /plan <feature-name>          -- plan a feature"
