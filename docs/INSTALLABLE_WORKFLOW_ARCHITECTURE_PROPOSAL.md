# Installable Workflow Architecture Proposal

## Status

Proposal for the next Pathly architecture increment.

Pathly should continue to be described as a public beta candidate until the
install, adapter, hook, and end-to-end smoke gates are verified on clean
machines.

## Problem Statement

Pathly already has the right core idea: files are the protocol, role contracts
define agent behavior, and the orchestrator is a deterministic filesystem state
machine. The current gap is product shape. A user should not need to clone the
repo, manually wire adapters, or understand host-specific plugin internals
before Pathly can help.

The target experience is:

```text
pip install pathly
pathly setup
```

After setup, the user should work from the AI coding tool they already use:

```text
Claude Code: /pathly add password reset
Codex:      Use Pathly to add password reset
CLI:        pathly go "add password reset"
```

Pathly remains the workflow brain. Claude Code, Codex, Copilot, and the CLI are
host surfaces.

## Proposed Solution

Move Pathly toward an installable package that owns setup, adapter materializing,
host detection, diagnostics, and portable workflow state. Keep adapters thin and
keep the FSM in Pathly core.

```text
User
 |
 v
Host chat or terminal
 |
 |  Claude Code: /pathly ...
 |  Codex:      Use Pathly ...
 |  CLI:        pathly ...
 v
+------------------------------------------------------+
| Pathly host adapter                                  |
| - command/skill wrapper                              |
| - host-specific metadata                             |
| - optional hook registration                         |
+--------------------------+---------------------------+
                           |
                           v
+------------------------------------------------------+
| Pathly core                                          |
|                                                      |
| Director                                             |
| - classifies user intent                             |
| - chooses the lightest safe workflow                 |
| - does not implement source changes                  |
|                                                      |
| Orchestrator FSM                                     |
| - reads disk                                         |
| - recovers effective state                           |
| - applies one event                                  |
| - writes state and event logs                        |
| - emits one next action                              |
|                                                      |
| Role contracts                                       |
| - planner, architect, builder, reviewer, tester      |
| - scout, quick, po, web-researcher, meet consults    |
+--------------------------+---------------------------+
                           |
                           v
+------------------------------------------------------+
| Target project workspace                             |
|                                                      |
| plans/<feature>/                                     |
| |-- USER_STORIES.md                                  |
| |-- IMPLEMENTATION_PLAN.md                           |
| |-- PROGRESS.md                                      |
| |-- CONVERSATION_PROMPTS.md                          |
| |-- STATE.json                                       |
| |-- EVENTS.jsonl                                     |
| |-- feedback/                                        |
| `-- consults/                                        |
+------------------------------------------------------+
```

## Architecture Layers

```text
Host layer
  Claude Code plugin, Codex plugin, CLI, future Copilot/Cursor/Windsurf
  |
  v
Adapter layer
  Thin wrappers that expose host-native commands and load core prompts
  |
  v
Core workflow layer
  Director, workflow prompts, role contracts, plan templates
  |
  v
Runtime layer
  Orchestrator reducer, event log, state recovery, hooks, runners
  |
  v
Project filesystem
  plans/<feature>/, feedback files, consult notes, source code changes
```

Core owns reusable behavior. Adapters own host packaging only. Runtime code
belongs in `pathly/` and `orchestrator/`; host-neutral prompts and role contracts
belong in `core/`.

## User Stories

### Story 1.1: One-command install

**As a** new user, **I want** to install Pathly with `pip install pathly`, **so
that** I can start using it without cloning the repository.

**Acceptance Criteria:**
- [ ] `pip install pathly` installs the CLI entry point.
- [ ] `pathly --version` reports the installed version.
- [ ] `pathly doctor` can run outside the Pathly source checkout.
- [ ] Package data includes core prompts, role contracts, templates, and adapter
      assets.

**Edge Cases:**
- User has no Claude Code or Codex installed.
- User installs in a virtual environment.
- User installs globally but runs Pathly from any project directory.

**Delivered by:** Phase 1 -> Conversation 1

### Story 1.2: Guided setup

**As a** user, **I want** `pathly setup` to detect my available AI coding tools,
**so that** Pathly can install the right adapters and tell me exactly how to
start.

**Acceptance Criteria:**
- [ ] `pathly setup` detects supported hosts.
- [ ] `pathly setup claude` installs or prints the Claude Code setup path.
- [ ] `pathly setup codex` installs or prints the Codex marketplace setup path.
- [ ] `pathly setup --no-hooks` skips hook registration.
- [ ] Setup output ends with host-specific start commands.

**Edge Cases:**
- Multiple supported hosts are installed.
- No supported host is installed.
- Existing Pathly adapter files are present from an older version.

**Delivered by:** Phase 2 -> Conversation 2

### Story 1.3: Host chat remains the control surface

**As a** user, **I want** to talk to Pathly from Claude Code, Codex, or the CLI,
**so that** I do not need a separate Pathly chat application.

**Acceptance Criteria:**
- [ ] Claude Code docs show `/pathly ...` and `/path ...`.
- [ ] Codex docs show `Use Pathly ...`, not `/pathly ...`.
- [ ] CLI docs show `pathly go`, `pathly flow`, `pathly help`, and
      `pathly doctor`.
- [ ] The user-facing route is Director first unless a direct route is explicit.

**Edge Cases:**
- Codex does not confidently select the Pathly skill.
- Claude Code plugin is installed but hooks are not.
- User chooses CLI fallback only.

**Delivered by:** Phase 3 -> Conversation 3

### Story 1.4: Deterministic FSM control

**As a** maintainer, **I want** the orchestrator to own all lifecycle state
transitions, **so that** agent handoffs stay recoverable and inspectable.

**Acceptance Criteria:**
- [ ] Director routes but does not implement.
- [ ] Orchestrator reads `STATE.json`, `EVENTS.jsonl`, `PROGRESS.md`, and
      feedback files before acting.
- [ ] Orchestrator applies one event and emits one next action.
- [ ] Known feedback files block forward progress.
- [ ] State can be reconstructed from disk after process restart.

**Edge Cases:**
- `STATE.json` disagrees with feedback files.
- `EVENTS.jsonl` is missing or partially corrupt.
- Multiple feedback files exist at the same time.

**Delivered by:** Phase 4 -> Conversation 4

### Story 1.5: Safe hooks

**As a** maintainer, **I want** hooks to perform small deterministic checks, **so
that** they improve safety without secretly running the whole workflow.

**Acceptance Criteria:**
- [ ] Hooks can classify feedback and add metadata.
- [ ] Hooks can run a quick FSM validity check.
- [ ] Hooks do not spawn long multi-agent workflows.
- [ ] Hook writes are path-validated under the active project.
- [ ] Hook failures are visible but do not corrupt state.

**Edge Cases:**
- Hook payload is malformed.
- Hook target path is outside `plans/`.
- Hook host does not support a documented native hook schema.

**Delivered by:** Phase 5 -> Conversation 5

### Story 1.6: Controlled subagent use

**As a** maintainer, **I want** lifecycle agents to be spawned only through the
orchestrator, **so that** the FSM remains the authority.

**Acceptance Criteria:**
- [ ] Only the orchestrator spawns lifecycle roles.
- [ ] Builder may use bounded helper consults such as `scout` or `quick`.
- [ ] Helper consults do not move FSM state.
- [ ] `po` remains optional and on-demand.
- [ ] `architect` remains on-demand unless real design uncertainty exists.
- [ ] `meet` remains read-only and excludes `director` as a default target.

**Edge Cases:**
- Builder needs to read many files before editing.
- Reviewer identifies an architecture violation.
- User asks for a read-only role consultation mid-flow.

**Delivered by:** Phase 6 -> Conversation 6

## Target User Flow

```text
1. Install

   pip install pathly
   pathly setup

2. Setup detects hosts

   Claude Code: found
   Codex:      found
   Hooks:      optional

3. User opens normal coding tool

   Claude Code:
     /pathly add password reset

   Codex:
     Use Pathly to add password reset

4. Director routes

   Request type: feature
   Rigor: lite
   Entry: planning

5. Orchestrator starts FSM

   Read disk
   Recover state
   Apply COMMAND event
   Write EVENTS.jsonl and STATE.json
   Emit next action: planner

6. Specialist agent acts

   Planner writes plan files
   Builder implements scoped conversations
   Reviewer writes feedback or PASS
   Tester verifies acceptance criteria

7. Files control handoff

   feedback/REVIEW_FAILURES.md exists -> route to builder
   feedback/ARCH_FEEDBACK.md exists   -> route to architect
   no feedback and all work done      -> route to tester/retro
```

## FSM Flow

```text
IDLE
 |
 | user request
 v
DIRECTOR_ROUTING
 |
 | route selected
 v
PLANNING
 |
 | plan files written
 v
PLAN_PAUSED
 |
 | continue
 v
BUILDING
 |
 | builder completes next conversation
 v
REVIEWING
 |
 |------------------------------+
 | feedback exists              |
 v                              |
BLOCKED_ON_FEEDBACK             |
 |                              |
 | route to owner               |
 v                              |
PLANNER / ARCHITECT / BUILDER   |
 |                              |
 | feedback deleted             |
 +------------------------------+
 |
 v
IMPLEMENT_PAUSED
 |
 | more TODO conversations
 v
BUILDING
 |
 | all conversations done
 v
TESTING
 |
 | tests pass
 v
TEST_PAUSED
 |
 v
RETRO
 |
 v
DONE
```

## Hook Policy

Hooks are guardrails, not the main workflow driver.

Allowed hook responsibilities:

- Add TTL or metadata to known feedback files.
- Classify `IMPL_QUESTIONS.md` into requirement or architecture questions.
- Split architecture questions into `DESIGN_QUESTIONS.md`.
- Validate that writes remain under the active project `plans/` directory.
- Emit visible diagnostics for stale state or malformed payloads.
- Run fast FSM consistency checks.

Disallowed hook responsibilities:

- Secretly run an entire feature pipeline.
- Spawn long-running lifecycle agents after every file write.
- Advance past feedback without the orchestrator.
- Edit source code.
- Treat unsupported host hook schemas as implemented.

Suggested hook flow:

```text
Agent writes feedback/IMPL_QUESTIONS.md
 |
 v
Host PostToolUse hook
 |
 v
pathly hooks run post-tool-use
 |
 v
Validate payload and path
 |
 v
Classify/split feedback or emit diagnostic
 |
 v
Return control to host chat
 |
 v
Orchestrator reads updated files on the next workflow step
```

## Subagent Policy

The orchestrator owns lifecycle delegation.

```text
Allowed:

Orchestrator -> planner
Orchestrator -> architect
Orchestrator -> builder
Orchestrator -> reviewer
Orchestrator -> tester
Orchestrator -> quick retro summary

Builder -> scout helper       (read-only, bounded question)
Builder -> quick helper       (small lookup, max 1-2 tool calls)
Builder -> meet consult       (read-only consult note)
```

```text
Avoid:

Builder -> reviewer -> architect -> builder
```

That pattern creates uncontrolled agent-to-agent conversation and bypasses FSM
state. If a role needs another lifecycle role, it should write a feedback file
or consult note. The orchestrator routes the next action.

## Packaging And Setup Plan

### Phase 1: Package data loading

**Purpose:** Make installed Pathly independent of a source checkout.

**Dependencies:** Existing `pyproject.toml` package data and CLI entry point.

**Enables:** `pip install pathly` can expose prompts, templates, adapters, and
CLI behavior from package resources.

**Tasks:**
- Move installer code away from repo-relative assumptions where needed.
- Add package-resource helpers using `importlib.resources`.
- Confirm core prompts, agent contracts, plan templates, and adapter assets are
  included in built wheels.
- Add tests that install/build from a temporary wheel or isolated package path.

**Verification:**
- `python -m build`
- Install built wheel in a temporary environment.
- `pathly doctor`
- `pathly help`

### Phase 2: Unified setup command

**Purpose:** Give users one guided setup entry point.

**Dependencies:** Phase 1 package data loading.

**Enables:** `pathly setup`, `pathly setup claude`, and `pathly setup codex`.

**Tasks:**
- Add a `setup` command separate from low-level `install` compatibility.
- Detect Claude Code and Codex availability.
- Materialize adapter files into a user-level Pathly data directory.
- Register Claude/Codex adapters using host-supported mechanisms.
- Add `--no-hooks`, `--force`, and dry-run behavior.

**Verification:**
- Focused CLI tests for setup routing.
- Temp-home tests for generated files.
- Existing `pytest -q`.

### Phase 3: Host-specific start guidance

**Purpose:** Make it obvious where the user should talk to Pathly.

**Dependencies:** Phase 2 setup output.

**Enables:** Clear start commands per host.

**Tasks:**
- Update README install section.
- Update adapter READMEs.
- Add `pathly status` or improve `pathly help` to show current host guidance.
- Keep Codex wording as natural language, not slash commands.

**Verification:**
- Packaging tests assert README commands map to real routes.
- Manual smoke in Claude Code and Codex.

### Phase 4: FSM status and recovery UX

**Purpose:** Make machine state visible without exposing unnecessary internals.

**Dependencies:** Existing orchestrator state/event packages.

**Enables:** Users can understand "what is next" after interruption.

**Tasks:**
- Add or refine `pathly status [feature]`.
- Summarize current state, active feedback, next owner, and suggested command.
- Keep raw event names hidden unless diagnostics are requested.
- Add tests for missing state, recovered state, feedback-blocked state, and done.

**Verification:**
- Focused status tests.
- `pytest -q`.

### Phase 5: Hook hardening

**Purpose:** Make hooks safe enough for broader beta use.

**Dependencies:** Existing hook runtime and contracts.

**Enables:** Optional automation without hidden workflow execution.

**Tasks:**
- Canonicalize hook target paths.
- Ensure hook writes stay under the active project `plans/` directory.
- Add visible diagnostics for hook failures.
- Keep unsupported hosts returning explicit unavailable config.
- Add tests for malformed JSON, ignored paths, path traversal, missing API key,
  already-tagged feedback, and split architecture questions.

**Verification:**
- `pytest tests/test_hooks.py -q`
- `pytest -q`

### Phase 6: Subagent and consult policy enforcement

**Purpose:** Prevent lifecycle routing from becoming uncontrolled agent chat.

**Dependencies:** Existing role contracts and `meet` workflow.

**Enables:** Builder-side help without bypassing the orchestrator.

**Tasks:**
- Update role contracts with lifecycle versus helper subagent rules.
- Keep `po` optional and on-demand.
- Keep `architect` tied to real design uncertainty.
- Keep `meet` read-only and exclude `director` as a default target.
- Add static tests for critical prompt clauses.

**Verification:**
- Prompt/static contract tests.
- `pytest -q`.

## Conversation Breakdown

| Conv | Phase | Purpose | Dependencies | Enables | Verify |
|---|---|---|---|---|---|
| 1 | Package data loading | Installed package can find its own assets | Existing package data | No source checkout required | `python -m build`; temp install smoke |
| 2 | Unified setup command | One setup entry point | Conv 1 | `pathly setup` | CLI setup tests |
| 3 | Host start guidance | Clear user chat surface | Conv 2 | Better onboarding | README/adapter tests; manual smoke |
| 4 | FSM status UX | Show current state and next action | Existing FSM | Recovery clarity | Status tests |
| 5 | Hook hardening | Safe optional automation | Existing hooks | Safer beta | Hook tests |
| 6 | Subagent policy | Bound helper agents and consults | Existing role docs | FSM remains authority | Static prompt tests |

## Acceptance Criteria

- [ ] The document states that Director is the front door.
- [ ] The document states that Orchestrator owns FSM transitions.
- [ ] The document states that filesystem state is the source of truth.
- [ ] The document explains where the user chats for Claude Code, Codex, and CLI.
- [ ] The document defines hook responsibilities and hook boundaries.
- [ ] The document defines lifecycle agent and helper subagent policy.
- [ ] The document keeps `po` optional and on-demand.
- [ ] The document keeps `architect` on-demand unless risk requires it.
- [ ] The document keeps `meet` read-only and excludes `director` as a default
      consult target.
- [ ] The document includes a phased implementation plan with purpose,
      dependencies, what each phase enables, and verification.
- [ ] The document does not claim Pathly is production-ready.

