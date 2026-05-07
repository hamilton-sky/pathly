# setup-hook.ps1 — Register Pathly feedback hooks in ~/.claude/settings.json
# This is the ONLY thing that touches ~/.claude/ after plugin install.
# Run once after installing the plugin.
#
# Usage: .\scripts\setup-hook.ps1
#        .\scripts\setup-hook.ps1 -Remove   (to unregister)

param([switch]$Remove)

$PluginDir = "$env:USERPROFILE\.claude\plugins\pathly"
$ClassifyHookCmd = "python $PluginDir\hooks\classify_feedback.py"
$TtlHookCmd = "python $PluginDir\hooks\inject_feedback_ttl.py"
$Settings  = "$env:USERPROFILE\.claude\settings.json"
$SettingsDir = Split-Path -Parent $Settings

New-Item -ItemType Directory -Force -Path $SettingsDir | Out-Null

if (-not (Test-Path $Settings)) {
    '{}' | Out-File -FilePath $Settings -Encoding utf8
}

$Action = if ($Remove) { "--remove" } else { "" }

$PythonScript = @"
import json, sys, os

settings_file = r'$Settings'
hook_cmds = [
    r'$ClassifyHookCmd',
    r'$TtlHookCmd',
]
action = '$Action'

with open(settings_file) as f:
    try:
        settings = json.load(f)
    except Exception:
        settings = {}

hooks = settings.setdefault('hooks', {}).setdefault('PostToolUse', [])

def hook_command(h):
    commands = [
        hh.get('command', '')
        for hh in h.get('hooks', [])
    ]
    return commands[0] if commands else ''

def is_our_hook(h):
    return h.get('matcher') == 'Write' and any(
        script in hook_command(h)
        for script in ('classify_feedback.py', 'inject_feedback_ttl.py')
    )

if action == '--remove':
    before = len(hooks)
    settings['hooks']['PostToolUse'] = [h for h in hooks if not is_our_hook(h)]
    after = len(settings['hooks']['PostToolUse'])
    if before != after:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print('Hook removed from settings.json')
    else:
        print('Hook was not registered -- nothing to remove')
else:
    existing = {hook_command(h) for h in hooks if h.get('matcher') == 'Write'}
    added = []
    for hook_cmd in hook_cmds:
        if hook_cmd in existing:
            continue
        hooks.append({
            'matcher': 'Write',
            'hooks': [{'type': 'command', 'command': hook_cmd}]
        })
        added.append(hook_cmd)
    if added:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print('Hooks registered in settings.json')
        for hook_cmd in added:
            print(f'Command: {hook_cmd}')
    else:
        print('Hooks already registered in settings.json -- skipped')
"@

$PythonScript | python -
