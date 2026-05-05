# install.ps1 — Pathly installer for Claude Code
#
# Usage:
#   .\install.ps1              # install
#   .\install.ps1 -Uninstall   # remove
#
# What it installs:
#   adapters\claude-code\skills\ -> %USERPROFILE%\.claude\skills\ (slash commands)
#   adapters\claude-code\agents\ -> %USERPROFILE%\.claude\agents\ (sub-agents)
#   hooks\    -> %USERPROFILE%\.claude\plugins\pathly\hooks\
#
# After install, register the feedback hook (optional):
#   .\scripts\setup-hook.ps1

param([switch]$Uninstall)

$ClaudeDir = "$env:USERPROFILE\.claude"
$PluginName = "pathly"
$LegacyPluginName = "claude-agents-framework"
$ScriptDir = $PSScriptRoot
$ClaudeSkillSource = Join-Path $ScriptDir "adapters\claude-code\skills"
$ClaudeAgentSource = Join-Path $ScriptDir "adapters\claude-code\agents"
$CoreTemplateSource = Join-Path $ScriptDir "core\templates"

Write-Host ""
Write-Host "Pathly"
Write-Host "======"
Write-Host ""

if ($Uninstall) {
    Write-Host "Uninstalling..."
    Get-ChildItem $ClaudeSkillSource -Directory | ForEach-Object {
        $dest = "$ClaudeDir\skills\$($_.Name)"
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Write-Host "  - /$($_.Name)"
    }
    Get-ChildItem $ClaudeAgentSource -Filter "*.md" | ForEach-Object {
        $dest = "$ClaudeDir\agents\$($_.Name)"
        if (Test-Path $dest) { Remove-Item -Force $dest }
        Write-Host "  - $($_.Name)"
    }
    $pluginDir = "$ClaudeDir\plugins\$PluginName"
    if (Test-Path $pluginDir) { Remove-Item -Recurse -Force $pluginDir }
    $legacyPluginDir = "$ClaudeDir\plugins\$LegacyPluginName"
    if (Test-Path $legacyPluginDir) { Remove-Item -Recurse -Force $legacyPluginDir }
    Write-Host ""
    Write-Host "Uninstalled. Run '.\scripts\setup-hook.ps1 -Remove' to remove the hook."
    Write-Host ""
    exit 0
}

# Skills
Write-Host "Installing skills..."
New-Item -ItemType Directory -Force -Path "$ClaudeDir\skills" | Out-Null
Get-ChildItem $ClaudeSkillSource -Directory | ForEach-Object {
    $dest = "$ClaudeDir\skills\$($_.Name)"
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    Copy-Item -Recurse $_.FullName $dest
    Write-Host "  + /$($_.Name)"
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

# Hooks runtime
Write-Host ""
Write-Host "Installing hooks..."
$hooksDir = "$ClaudeDir\plugins\$PluginName\hooks"
New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
Get-ChildItem "$ScriptDir\hooks" -Filter "*.py" | ForEach-Object {
    Copy-Item -Force $_.FullName "$hooksDir\$($_.Name)"
    Write-Host "  + $($_.Name)"
}

Write-Host ""
Write-Host "Done. Installed to $ClaudeDir"
Write-Host ""
Write-Host "Next step -- register the feedback hook (optional):"
Write-Host "  .\scripts\setup-hook.ps1"
Write-Host ""
