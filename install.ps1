# Claude Agents Framework — Windows installer
# Copies agents, skills, and templates into ~/.claude/
# Safe: backs up any existing files before overwriting.

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
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
New-Item -ItemType Directory -Path "$ClaudeDir\agents" -Force | Out-Null
New-Item -ItemType Directory -Path "$ClaudeDir\templates\plan" -Force | Out-Null

# Install agents
Write-Host "Installing agents..."
Copy-Item "$RepoDir\agents\*.md" "$ClaudeDir\agents\" -Force -Verbose

# Install skills (merge)
Write-Host ""
Write-Host "Installing skills..."
Get-ChildItem "$RepoDir\skills" -Directory | ForEach-Object {
    $skillName = $_.Name
    New-Item -ItemType Directory -Path "$ClaudeDir\skills\$skillName" -Force | Out-Null
    Copy-Item "$($_.FullName)\SKILL.md" "$ClaudeDir\skills\$skillName\SKILL.md" -Force -Verbose
}

# Install templates
Write-Host ""
Write-Host "Installing plan templates..."
Copy-Item "$RepoDir\templates\plan\*.md" "$ClaudeDir\templates\plan\" -Force -Verbose

# Install docs
Write-Host ""
Write-Host "Installing docs..."
Copy-Item "$RepoDir\docs\*.md" "$ClaudeDir\" -Force -Verbose

Write-Host ""
Write-Host "==================================="
Write-Host "Install complete."
Write-Host ""
$agentCount = (Get-ChildItem "$ClaudeDir\agents\*.md" -ErrorAction SilentlyContinue).Count
$skillCount  = (Get-ChildItem "$ClaudeDir\skills" -Directory -ErrorAction SilentlyContinue).Count
$tmplCount   = (Get-ChildItem "$ClaudeDir\templates\plan\*.md" -ErrorAction SilentlyContinue).Count
Write-Host "Agents installed   : $agentCount"
Write-Host "Skills installed   : $skillCount"
Write-Host "Templates installed: $tmplCount"
Write-Host ""
Write-Host "Start a new Claude Code session in any project and run:"
Write-Host "  /team-flow <feature-name>   -- full pipeline with feedback loops"
Write-Host "  /storm                      -- brainstorm a feature"
Write-Host "  /plan <feature-name>        -- plan a feature"
