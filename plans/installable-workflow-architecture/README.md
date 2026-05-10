# Feature Plan: installable-workflow-architecture

## What this folder is

This is the implementation plan package for the **installable-workflow-architecture** feature.
It is a Pathly-standard feature plan folder: a set of structured documents that guide a
builder through a multi-conversation implementation. It does not contain code.

**Status: NOT STARTED** — all 4 conversations are TODO.

---

## What the feature does

Makes Pathly installable from `pip install pathly` without requiring users to clone the
repository or manually wire host adapter files.

Today Pathly works but assumes a source checkout. This feature adds:
- A package resource API so Pathly finds its own assets from an installed wheel
- `pathly setup` / `pathly setup --dry-run` / `pathly setup --apply` — transparent setup
  with a report-before-mutate contract
- `pathly status [feature]` and improved `pathly doctor` — actionable recovery UX
- Versioned adapter snapshot materialization into user data locations
- Hardened hooks that stay bounded guardrails (no hidden workflow automation)

---

## Files in this folder

| File | Purpose |
|---|---|
| [README.md](README.md) | This file — orientation for the feature plan folder |
| [ARCHITECTURE_PROPOSAL.md](ARCHITECTURE_PROPOSAL.md) | Design decisions, layer breakdown, target modules, risks |
| [USER_STORIES.md](USER_STORIES.md) | 7 user stories (S1.1–S4.1) with acceptance criteria and edge cases |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Phase-by-phase implementation detail for the builder |
| [CONVERSATION_PROMPTS.md](CONVERSATION_PROMPTS.md) | Exact prompts to paste to drive each of the 4 builder conversations |
| [PROGRESS.md](PROGRESS.md) | Live status tracker — story status, conversation status, phase detail |
| [HAPPY_FLOW.md](HAPPY_FLOW.md) | Step-by-step ideal user journey from `pip install` to workflow recovery |
| [EDGE_CASES.md](EDGE_CASES.md) | Edge cases and failure modes that the implementation must handle |
| [FLOW_DIAGRAM.md](FLOW_DIAGRAM.md) | Visual diagram of the new layer and command flow |

---

## Conversation breakdown

| Conv | Stories | What gets built | Verify gate |
|---|---|---|---|
| 1 | S1.1, S1.2 | Package resource API + clean install smoke + `pathly --version` | `python -m build`; installed-wheel smoke; `pytest tests/test_cli.py tests/test_project_packaging.py -q` |
| 2 | S2.1, S2.2 | `pathly setup` dry-run + adapter materialization | `pytest tests/test_setup.py tests/test_cli.py -q`; `pathly setup --dry-run` |
| 3 | S3.1, S3.2 | `pathly status` + `pathly doctor` + hook hardening | `pytest tests/test_cli.py tests/test_hooks.py -q`; `pathly status`; `pathly doctor` |
| 4 | S4.1 | Host smoke + docs alignment | `pytest -q`; host smoke matrix |

Each conversation must leave the codebase runnable and testable before the next begins.

---

## Key design constraints

- **Setup defaults to report mode** — `pathly setup` never mutates without `--apply`
- **Setup is not workflow authority** — it installs surfaces; the orchestrator owns lifecycle
- **Hooks stay bounded** — hooks validate and emit diagnostics only; they never advance FSM state
- **Versioned snapshots** — adapter assets are copied into versioned user data locations, not
  registered directly from the package install location

---

## How to start

Paste the Conversation 1 prompt from [CONVERSATION_PROMPTS.md](CONVERSATION_PROMPTS.md) into
a fresh Claude Code conversation. Commit after each conversation before starting the next.
