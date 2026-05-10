# pathly-skills-install — Progress

## Status: NOT STARTED

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1.1 | stitch_skill() function | Conv 1 | TODO |
| S1.2 | Skills section in install.yaml + _run_host() wiring | Conv 1 | TODO |
| S2.1 | Canonical skill bodies — start and end | Conv 2 | TODO |
| S2.2 | Skill YAML metadata — Claude adapter | Conv 2 | TODO |
| S2.3 | Skill YAML metadata — Codex and Copilot adapters | Conv 2 | TODO |
| S3.1 | Tests for stitch_skill() | Conv 3 | TODO |

## Conversation Breakdown

| Conv | Phases | Stories | Status | Verify |
|------|--------|---------|--------|--------|
| 1 | 1-2 | S1.1, S1.2 | TODO | `cd pathly-adapters && pytest tests/test_stitch.py -x` + `pathly-setup --dry-run` |
| 2 | 3-5 | S2.1, S2.2, S2.3 | TODO | `pathly-setup --dry-run` shows 5 skill files per host |
| 3 | 6 | S3.1 | TODO | `cd pathly-adapters && pytest -x` |

See **CONVERSATION_PROMPTS.md** for exact prompts to paste in each conversation.

## Phase Detail

| # | Phase | Layer | Description | Conv | Status | Key Files |
|---|-------|-------|-------------|------|--------|-----------|
| 1 | stitch_skill + resources | install_cli | Add stitch_skill(), core_skills_path() | 1 | TODO | `install_cli/stitch.py`, `install_cli/resources.py` |
| 2 | install.yaml + _run_host() wiring | install_cli + config | Skills section in install.yaml, skill loop in _run_host() | 1 | TODO | `install_cli/setup_command.py`, `adapters/*/install.yaml` |
| 3 | core skill bodies | core/skills | Create start.md and end.md | 2 | TODO | `core/skills/start.md`, `core/skills/end.md` |
| 4 | Claude skill YAMLs | adapters/claude/_meta | 5 skill YAML files for claude | 2 | TODO | `adapters/claude/_meta/*_skill.yaml` |
| 5 | Codex + Copilot skill YAMLs | adapters/codex,copilot/_meta | 5+5 skill YAML files | 2 | TODO | `adapters/codex/_meta/*_skill.yaml`, `adapters/copilot/_meta/*_skill.yaml` |
| 6 | Tests | tests | test_stitch_skill.py | 3 | TODO | `tests/test_stitch_skill.py` |

## Prerequisites
- stitch_agent() and materialize() implemented ✓
- core/skills/ with 18 bodies exists ✓
- adapters/<host>/_meta/ directories exist ✓

## Blocked By
- Nothing
