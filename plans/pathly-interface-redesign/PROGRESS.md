# pathly-interface-redesign — Progress

## Status: IN PROGRESS

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1.1 | `/pathly start` — no-argument flow entry | Conv 1 | DONE |
| S1.2 | `/pathly continue` — no-argument flow resume | Conv 1 | DONE |
| S1.3 | `/pathly end` — no-argument flow close | Conv 1 | DONE |
| S2.1 | `/pathly meet` — no-argument mid-flow consultation | Conv 1 | DONE |
| S2.2 | `/pathly help` — context-aware state display | Conv 1 | DONE |
| S3.1 | Agent meta YAML — thin adapter files | Conv 2 | DONE |
| S3.2 | Agent capability matrix — explicit `can_spawn` | Conv 2 | DONE |
| S4.1 | Install-time stitching — no committed generated files | Conv 3 | TODO |

## Conversation Breakdown

| Conv | Phases | Stories | Depends On | Status | Verify |
|------|--------|---------|------------|--------|--------|
| 1 | Phases 1-3 | S1.1, S1.2, S1.3, S2.1, S2.2 | None | DONE | Manual smoke: type each `/pathly [verb]`, confirm routing. `pytest tests/test_cli.py -q` |
| 2 | Phases 1-4 | S3.1, S3.2 | Conv 1 DONE | DONE | `python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('adapters/**/_meta/*.yaml', recursive=True)]"` |
| 3 | Phases 1-4 | S4.1 | Conv 2 DONE | TODO | `pytest tests/test_stitch.py -q`; `pathly install --dry-run` shows N agents, no errors |

See **CONVERSATION_PROMPTS.md** for exact prompts to paste in each conversation.

## Phase Detail

| # | Phase | Layer | Description | Conv | Status | Key Files |
|---|-------|-------|-------------|------|--------|-----------|
| 1 | Verb router update | core/skills | Update `core/skills/pathly.md` to route 5 no-argument verbs | 1 | DONE | `core/skills/pathly.md` |
| 2 | Help menu update | core/skills | Update `core/skills/help.md` to use `/pathly [verb]` syntax | 1 | DONE | `core/skills/help.md` |
| 3 | End verb behavior | core/skills | Add `/pathly end` routing to orchestrator retro entry | 1 | DONE | `core/skills/pathly.md`, `core/skills/team-flow.md` |
| 4 | Meta YAML format definition | adapters | Define and document canonical meta YAML format | 2 | DONE | `adapters/claude/_meta/`, format spec |
| 5 | Claude meta files | adapters/claude | Create `_meta/*.yaml` for all 12 agents — Claude adapter | 2 | DONE | `adapters/claude/_meta/*.yaml` |
| 6 | Codex + Copilot meta files | adapters/codex, adapters/copilot | Create `_meta/*.yaml` for all agents — Codex + Copilot | 2 | DONE | `adapters/codex/_meta/*.yaml`, `adapters/copilot/_meta/*.yaml` |
| 7 | Strip adapter agent files | adapters | Remove duplicated behavioral content from adapter agent files | 2 | DONE | `adapters/*/agents/*.md` |
| 8 | `stitch.py` implementation | pathly/cli | New module: stitch core agent + meta YAML → complete file | 3 | TODO | `pathly/cli/stitch.py` |
| 9 | Integrate stitcher into install | pathly/cli | Update `pathly install` to stitch, add `--dry-run` validation | 3 | TODO | `pathly/cli/setup_command.py` |
| 10 | Gitignore generated files | repo | Add adapter agent files to `.gitignore` | 3 | TODO | `.gitignore` |
| 11 | Stitch tests | tests | `tests/test_stitch.py` — unit tests for stitcher | 3 | TODO | `tests/test_stitch.py` |

## Prerequisites

- `core/agents/*.md` files are complete and contain no platform-specific spawn syntax
- `adapters/claude/agents/*.md` files exist as reference for extracting current spawn sections into meta YAMLs
- `pathly install` (or `pathly setup --apply`) exists and copies files to destinations

## Blocked By

- Nothing. Conv 1 can start immediately.

## Coordination Note

Conv 3 of this plan changes what `pathly install` materializes. Coordinate with `installable-workflow-architecture` Conv 2 (adapter materialization) — that conv should use the stitcher output, not raw adapter files.
