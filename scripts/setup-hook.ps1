# setup-hook.ps1 — Register the classify_feedback hook in ~/.claude/settings.json
# This is the ONLY thing that touches ~/.claude/ after plugin install.
# Run once after installing the plugin.
#
# Usage: .\scripts\setup-hook.ps1
#        .\scripts\setup-hook.ps1 -Remove   (to unregister)

param([switch]$Remove)

$PluginDir = "$env:USERPROFILE\.claude\plugins\pathly"
$HookCmd   = "python $PluginDir\hooks\classify_feedback.py"
$Settings  = "$env:USERPROFILE\.claude\settings.json"

if (-not (Test-Path $Settings)) {
    '{}' | Out-File -FilePath $Settings -Encoding utf8
}

$Action = if ($Remove) { "--remove" } else { "" }

$PythonScript = @"
import json, sys, os

settings_file = r'$Settings'
hook_cmd = r'$HookCmd'
action = '$Action'

with open(settings_file) as f:
    try:
        settings = json.load(f)
    except Exception:
        settings = {}

hooks = settings.setdefault('hooks', {}).setdefault('PostToolUse', [])

def is_our_hook(h):
    return h.get('matcher') == 'Write' and any(
        'classify_feedback.py' in hh.get('command', '')
        for hh in h.get('hooks', [])
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
    if any(is_our_hook(h) for h in hooks):
        print('Hook already registered in settings.json -- skipped')
    else:
        hooks.append({
            'matcher': 'Write',
            'hooks': [{'type': 'command', 'command': hook_cmd}]
        })
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print('Hook registered in settings.json')
        print(f'Command: {hook_cmd}')
"@

python $PythonScript
