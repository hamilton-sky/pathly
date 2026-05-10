# Codex Agent Definitions

Codex adapter wrappers around the canonical role contracts in `core/agents/`.

The behavioral source of truth is in `core/agents/`. This directory adds Codex-specific
delegation patterns and removes Claude Code-only syntax (`tools:` lists, `Agent()` calls,
Claude model names).

When changing how an agent thinks, edit the matching `core/agents/<agent>.md` first,
then sync this adapter file.

## Role Map

| Agent | Role | Invoke when |
|---|---|---|
| director | director | Natural-language entry; classifies request, chooses workflow |
| architect | architect | Technical design, layer decisions, trade-offs |
| po | po | Requirements discussion, scope probing, PRD validation |
| planner | product-owner | User stories, conversation decomposition, plans/ folder |
| builder | executor | Coding, verification, staying in scope |
| tester | tester | Verifying acceptance criteria, test coverage |
| reviewer | reviewer | Adversarial review, finding violations |
| quick | analyst | Fast lookups, short summaries, focused tasks |
| orchestrator | orchestrator | FSM state recovery, pipeline routing |
| scout | analyst | Read-only codebase investigation |
| web-researcher | analyst | Web-only research for external docs and patterns |

## Key Difference From Claude Code Adapter

Claude Code agents use `tools: [Agent]` frontmatter and `Agent(subagent_type=...)` API.
Codex agents use natural language delegation patterns — see each file for details.
