# System Review

This is an internal review note for Pathly's current repository shape and
release posture. It is not a replacement for the architecture and readiness
docs.

## Current Strengths

- Files are the protocol: plans, feedback files, `STATE.json`, and
  `EVENTS.jsonl` make workflow state inspectable and recoverable.
- Role contracts are explicit: planner plans, builder implements, reviewer
  reports, tester verifies, and orchestrator routes.
- The repository now separates shared content from host packaging:
  `core/` owns reusable prompts and role contracts, while `adapters/` owns
  Claude Code, Codex, and CLI-facing wrappers.
- The Python package exposes a real `pathly` CLI through `pathly.cli:main`.
- Codex support has both a plugin adapter and a direct `.agents/skills/`
  compatibility mirror.

## Current Risks

- Pathly is still a public beta candidate, not production-ready.
- End-to-end agent behavior still needs manual smoke validation in Claude Code
  and Codex before broad release claims.
- Hook path validation and observability need hardening before hooks should be
  treated as production automation.
- The `meet` CLI depends on the `claude` command for read-only consultation at
  runtime, while Codex uses the skill workflow layer.
- Some older archived plans may mention pre-adapter paths; treat those as
  historical artifacts and prefer current `core/` plus `adapters/` paths.

## Design Decisions To Preserve

- Keep `po` optional and on-demand.
- Keep `architect` consultation tied to real design uncertainty or risk.
- Keep builder consultation constrained to specific questions and outputs.
- Keep `meet` read-only by default; it writes consult notes, not source code.
- Keep `director` out of the default `meet` target list.
- Keep core prompts host-neutral; adapters own slash-command or plugin syntax.

## Current Implementation Map

```text
README.md                         public overview and install guidance
pyproject.toml                    Python package, console script, data files
pathly/cli/                       CLI parser and command implementations
pathly/team_flow/                 Python team-flow driver
pathly/hooks/                     portable hook runner and hook handlers
pathly/runners/                   Claude/Codex runner abstractions
orchestrator/                     FSM states, events, reducer, event log
core/prompts/                     canonical workflow instructions
core/agents/                      canonical role contracts
core/templates/plan/              plan file templates
adapters/claude-code/             Claude plugin package
adapters/codex/                   Codex plugin package
.agents/                          Codex marketplace and direct skill mirror
tests/                            CLI, packaging, hooks, runners, FSM checks
```

## Recommended Next Hardening

1. Run clean-machine smoke tests for Claude Code and Codex install paths.
2. Add or maintain tests that validate every README command maps to a live
   parser command or adapter skill.
3. Add hook path canonicalization so hook writes are guaranteed to stay inside
   the intended project feedback directory.
4. Add timeout policy and tests for subprocess-backed runner calls.
5. Keep release docs and README wording at public beta until the smoke matrix
   and public walkthroughs exist.
