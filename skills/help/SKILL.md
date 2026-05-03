---
name: help
description: Show available commands, explain what each does, and detect the current project state to tell the user exactly what to run next.
argument-hint: "[feature-name — optional, to get state for a specific feature]"
model: haiku
---

## Step 1: Detect current state

Check the following in order:

1. Does `plans/STORM_SEED.md` exist? → storm was just run, next is `/plan`
2. Does `plans/$ARGUMENTS/` exist?
   - Read `plans/$ARGUMENTS/PROGRESS.md` if present
   - Are all conversations DONE? → next is `/retro $ARGUMENTS`
   - Is at least one conversation TODO? → next is `/build $ARGUMENTS`
3. Does `plans/$ARGUMENTS/feedback/` contain any open files? → report which agent needs to act
4. No plans folder at all → next is `/storm` or `/plan <feature>`

---

## Step 2: Print the state banner

```
═══════════════════════════════════════════
  Claude Agents Framework — Help
═══════════════════════════════════════════
```

If a feature was detected from state checks, print:

```
Current feature: <feature-name>
Status: <one of below>

  ● Storm done — ready to plan
      → /plan <feature>

  ● Planning done — ready to build
      Conversations: X done, Y remaining
      → /build <feature>         (next conversation only)
      → /team-flow <feature>     (full pipeline from here)

  ● Open feedback file: <filename>
      Needs: <which agent must act>
      → Tell Claude to act as that agent and resolve it

  ● All conversations done — ready for retro
      → /retro <feature>

  ● No active feature found
      → /storm                   (explore an idea first)
      → /plan <feature>          (skip storm, go straight to planning)
```

---

## Step 3: Print the full command reference

```
───────────────────────────────────────────
  PIPELINE COMMANDS
───────────────────────────────────────────

  /storm
      Architect (Opus) explores a feature idea.
      Produces: plans/STORM_SEED.md
      When: before planning, when the idea needs shaping.

  /plan <feature>
      Planner interviews you and researches the codebase.
      Produces: plans/<feature>/ with 8 files.
      When: you know what to build, need a structured plan.

  /build <feature>
      Builder implements the next TODO conversation.
      Updates: plans/<feature>/PROGRESS.md
      When: plan exists, ready to write code.

  /review
      Reviewer audits staged changes against your layer rules.
      Produces: feedback files if violations found.
      When: after writing code, before committing.

  /retro <feature>
      Quick writes a retrospective and seed for the next storm.
      Produces: plans/<feature>/RETRO.md
      When: all conversations are DONE.

  /team-flow <feature>
      Full pipeline: storm → plan → build loop → test → retro.
      Pauses at every stage for your approval.
      Add "auto" to skip pauses: /team-flow <feature> auto
      When: starting a feature end-to-end.

───────────────────────────────────────────
  BMAD INTEGRATION
───────────────────────────────────────────

  /prd-import <feature> <path/to/prd.md>
      Reads a BMAD PRD and generates all 8 plan files.
      Translates: ACs → verify commands
                  edge cases → workflow conversations
                  out-of-scope → Do NOT lists
      When: you have a BMAD PRD and want to skip the /plan interview.

───────────────────────────────────────────
  UTILITY
───────────────────────────────────────────

  /help [feature]
      Show this screen. Pass a feature name to see its current state.

───────────────────────────────────────────
  FEEDBACK FILES  (plans/<feature>/feedback/)
───────────────────────────────────────────

  File present = issue open. Deleted = resolved.

  ARCH_FEEDBACK.md     reviewer → architect   (blocking — stops all building)
  REVIEW_FAILURES.md   reviewer → builder     (fix before next conversation)
  IMPL_QUESTIONS.md    builder  → planner     (requirement unclear)
  DESIGN_QUESTIONS.md  builder  → architect   (technical blocker)
  TEST_FAILURES.md     tester   → builder     (AC failed or not covered)

───────────────────────────────────────────
  THE 8 AGENTS
───────────────────────────────────────────

  architect   opus    Layers, trade-offs, design decisions
  planner     sonnet  User stories, acceptance criteria, scope
  builder     sonnet  Implement exactly what was planned
  reviewer    sonnet  Find violations before they ship, never fix
  tester      sonnet  Verify ACs pass, report gaps
  discoverer  sonnet  Trace live sites, capture POM data
  orchestrator haiku  Sequence the pipeline, route feedback
  quick        haiku  Fast lookups, 2 tool calls max

───────────────────────────────────────────
  DOCS
───────────────────────────────────────────

  Full architecture:   docs/ARCHITECTURE_AGENTS.md
  Feedback protocol:   docs/FEEDBACK_PROTOCOL.md
  Philosophy:          docs/CONCEPTS.md
  Multi-tool roadmap:  docs/MULTI_TOOL_DESIGN.md
  GitHub repo:         https://github.com/hamilton-sky/claude-agents-framework

═══════════════════════════════════════════
```
