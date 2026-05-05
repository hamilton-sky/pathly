# Codex Adapter

Codex exposes Pathly as plugin skills, not as custom slash commands in current
Codex builds. Do not document `/pathly` as a Codex command unless a future Codex
release supports plugin-defined slash commands.

Use explicit natural-language skill prompts. These give Codex the strongest
signal to select the Pathly plugin:

```text
Use Pathly help
Use Pathly doctor on this project
Use Pathly to add password reset
Use Pathly to debug checkout button does nothing
Use Pathly to explore how auth state flows
Use Pathly flow for checkout-flow
```

Short forms may work when Codex confidently selects the plugin:

```text
Pathly help
Pathly doctor
Pathly add password reset
Pathly debug checkout button does nothing
Pathly explore how auth state flows
Pathly flow checkout-flow
```

If Codex responds by inspecting the current workspace instead of saying it is
using Pathly, the plugin was not selected. Retry with `Use Pathly ...`, confirm
Pathly is enabled in Settings -> Plugins, then restart Codex after changing a
local marketplace plugin.

Codex reserves slash commands such as `/help` for its own UI. If a user types
`/pathly`, current Codex versions may report it as an unrecognized command.

## Install Globally On One Machine

Codex local plugins are registered through a marketplace root. Once the
marketplace is added, Pathly is available from any Codex workspace on that
machine.

```powershell
git clone https://github.com/hamilton-sky/pathly
cd pathly
python -m pip install -e .

$market = "C:\tmp\pathly-marketplace"
New-Item -ItemType Directory -Path "$market\.agents\plugins" -Force
New-Item -ItemType Directory -Path "$market\plugins" -Force
New-Item -ItemType Junction -Path "$market\plugins\pathly" -Target (Get-Location)

# Write marketplace.json as shown in the root README, then:
codex plugin marketplace add $market
```

Every user needs their own local clone or installed package path. Do not point a
friend's Codex install at a path that only exists on your machine.

Recommended CLI fallback from inside a Codex workspace:

```text
pathly doctor
pathly init <feature>
pathly run <feature>
```

The live Codex plugin reads `adapters/codex/skills/`. These wrappers are
Codex-safe: they load the same canonical `core/prompts/*.md` workflows but do
not include Claude-only model frontmatter such as `haiku`, `sonnet`, or `opus`.
Core model intent should stay portable as `simple`, `normal`, or `advanced`;
Codex wrappers can map those tiers to Codex-native models only when that is
explicitly supported.

Claude Code keeps its own model-specific wrappers under
`adapters/claude-code/skills/` for the Claude plugin package.
