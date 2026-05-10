# Feature Plan: pathly-interface-redesign

## What this folder is

Implementation plan for the **pathly-interface-redesign** feature.
Standard rigor — 8 plan files, 3 conversations.

**Status: NOT STARTED** — all 3 conversations are TODO.

---

## What the feature does

Redesigns two layers of Pathly:

**1. No-argument verb surface** — Five uniform entry points that work identically on Claude Code, Codex, and Copilot:
- `/pathly start` → director decides scope and feature
- `/pathly continue` → orchestrator resumes from STATE.json
- `/pathly end` → orchestrator closes flow and triggers retro
- `/pathly meet` → mid-flow consultation with a specialist agent
- `/pathly help` → context-aware state display and menu

**2. Install-time agent stitching** — Eliminates duplicated behavioral content in adapter agent files:
- `core/agents/` contains behavioral contracts (single source of truth)
- `adapters/{platform}/_meta/{agent}.yaml` contains only frontmatter + spawn section
- `pathly install` stitches them together at install time
- No generated files committed to the repo

---

## Files

| File | Purpose |
|---|---|
| [README.md](README.md) | This file |
| [ARCHITECTURE_PROPOSAL.md](ARCHITECTURE_PROPOSAL.md) | Design decisions — verb surface, stitching, capability matrix |
| [USER_STORIES.md](USER_STORIES.md) | 8 stories (S1.1–S4.1) with acceptance criteria |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | 3 conversations, 11 phases |
| [CONVERSATION_PROMPTS.md](CONVERSATION_PROMPTS.md) | 3 self-contained builder prompts |
| [PROGRESS.md](PROGRESS.md) | Live status tracker |
| [HAPPY_FLOW.md](HAPPY_FLOW.md) | 5 ideal user journey scenarios |
| [EDGE_CASES.md](EDGE_CASES.md) | 14 edge cases and failure modes |
| [FLOW_DIAGRAM.md](FLOW_DIAGRAM.md) | ASCII diagrams — verb routing, stitching, capability matrix |

---

## Conversation breakdown

| Conv | Stories | What gets built | Verify |
|---|---|---|---|
| 1 | S1.1–S2.2 | No-argument verb router in `core/skills/pathly.md`, help menu updates | Manual smoke per verb; `pytest tests/test_cli.py -q` |
| 2 | S3.1–S3.2 | Agent meta YAML files for all platforms + strip adapter agent files | YAML parse validation script |
| 3 | S4.1 | `stitch.py`, install integration, `.gitignore`, stitch tests | `pytest tests/test_stitch.py -q`; `pathly install --dry-run` |

---

## Key constraints

- `core/agents/` is never modified — it is the behavioral source of truth
- Adapter agent files are stripped or deleted — they are generated artifacts
- No-argument verbs read state from files, not from CLI arguments
- `can_spawn` is content-injected into stitched files — not runtime-enforced
- Conv 3 must be coordinated with `installable-workflow-architecture` Conv 2

---

## How to start

Paste Conversation 1 prompt from [CONVERSATION_PROMPTS.md](CONVERSATION_PROMPTS.md) into a fresh Claude Code conversation. Commit after each conversation before starting the next.
