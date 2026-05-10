# install.ps1 — Pathly installer for Claude Code
#
# Usage:
#   .\install.ps1              # install
#   .\install.ps1 -Uninstall   # remove
#
# What it installs:
#   core\skills\ -> %USERPROFILE%\.claude\skills\ (slash commands)
#   adapters\claude\agents\ -> %USERPROFILE%\.claude\agents\ (sub-agents)
#
# After install, register the feedback hook (optional):
#   python -m pip install -e .
#   pathly hooks install claude

param([switch]$Uninstall)

$ClaudeDir = "$env:USERPROFILE\.claude"
$PluginName = "pathly"
$ScriptDir = $PSScriptRoot
$ClaudeSkillSource = Join-Path $ScriptDir "core\skills"
$ClaudeAgentSource = Join-Path $ScriptDir "adapters\claude\agents"
$CoreTemplateSource = Join-Path $ScriptDir "core\templates"

Write-Host ""
Write-Host "Pathly"
Write-Host "======"
Write-Host ""

if ($Uninstall) {
    Write-Host "Uninstalling..."
    Get-ChildItem $ClaudeSkillSource -Filter "*.md" | ForEach-Object {
        $dest = "$ClaudeDir\skills\$($_.Name)"
        if (Test-Path $dest) { Remove-Item -Force $dest }
        Write-Host "  - /$($_.BaseName)"
    }
    Get-ChildItem $ClaudeAgentSource -Filter "*.md" | ForEach-Object {
        $dest = "$ClaudeDir\agents\$($_.Name)"
        if (Test-Path $dest) { Remove-Item -Force $dest }
        Write-Host "  - $($_.Name)"
    }
    $pluginDir = "$ClaudeDir\plugins\$PluginName"
    if (Test-Path $pluginDir) { Remove-Item -Recurse -Force $pluginDir }
    Write-Host ""
    Write-Host "Uninstalled. Remove Pathly entries from ~/.claude/settings.json if desired."
    Write-Host ""
    exit 0
}

# Skills
Write-Host "Installing skills..."
New-Item -ItemType Directory -Force -Path "$ClaudeDir\skills" | Out-Null
Get-ChildItem $ClaudeSkillSource -Filter "*.md" | ForEach-Object {
    Copy-Item -Force $_.FullName "$ClaudeDir\skills\$($_.Name)"
    Write-Host "  + /$($_.BaseName)"
}

# Agents
Write-Host ""
Write-Host "Installing agents..."
New-Item -ItemType Directory -Force -Path "$ClaudeDir\agents" | Out-Null
Get-ChildItem $ClaudeAgentSource -Filter "*.md" | Where-Object { $_.Name -ne "README.md" } | ForEach-Object {
    Copy-Item -Force $_.FullName "$ClaudeDir\agents\$($_.Name)"
    Write-Host "  + $($_.Name)"
}

# Templates
Write-Host ""
Write-Host "Installing templates..."
$templatesDir = "$ClaudeDir\plugins\$PluginName\templates"
New-Item -ItemType Directory -Force -Path $templatesDir | Out-Null
Copy-Item -Recurse -Force "$CoreTemplateSource\*" $templatesDir
Write-Host "  + templates\plan\"

Write-Host ""
Write-Host "Done. Installed to $ClaudeDir"
Write-Host ""
Write-Host "Next step -- register the feedback hook (optional):"
Write-Host "  python -m pip install -e ."
Write-Host "  pathly hooks install claude"
Write-Host ""
