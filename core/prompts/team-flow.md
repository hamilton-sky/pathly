# team-flow

This is the canonical, tool-agnostic Pathly behavior for the team-flow workflow.
Adapter skills should load and follow this prompt instead of duplicating workflow logic.

## Pathly Command Surface

Use `/pathly <command>` as the canonical cross-framework command form. `/path <command>` is the short alias. Legacy direct skill commands may remain available in some hosts for backwards compatibility, but user-facing guidance should prefer `/pathly` or `/path`.

Run the full feature pipeline for `$ARGUMENTS`.

## Argument parsing

Parse `$ARGUMENTS` for these tokens (order doesn't matter):
- First word that is not a keyword = `FEATURE` (the feature name)
- `lite` → set `rigor = lite` (4 required plan files, fewer gates)
- `standard` → set `rigor = standard` (default current pipeline)
- `strict` → set `rigor = strict` (mandatory gates, audit logs)
- `nano` → set `mode = nano` (no plan files, builder + reviewer only, ≤ 2 files)
- `fast` → set `autoFlow = true` (no pause points)
- `plan` → set `entryStage = plan`
- `build` → set `entryStage = build`
- `test` → set `entryStage = test`
- Default: `entryStage = discovery`
- Default: `rigor = lite` (escalator may offer upgrade to standard after planning)

If both `strict` and `fast` are present, stop and report:
`strict mode requires human approval gates; remove fast or choose standard fast.`

If `nano` is present with `strict`, `standard`, or `plan`/`build`/`test` entry stages, stop and report:
`nano mode has no plan stages; remove the conflicting flag or choose lite instead.`

Examples:
```
/pathly flow hotel-search              ← full pipeline, path selector
/pathly flow hotel-search build        ← skip to build stage
/pathly flow hotel-search test         ← skip to test stage
/pathly flow hotel-search fast         ← full pipeline, no pauses
/pathly flow hotel-search build fast   ← resume build, no pauses
/pathly flow hotel-search lite         ← small change, 4-file plan, lighter gates
/pathly flow hotel-search strict       ← high-risk change, mandatory gates + audit
/pathly flow my-fix nano               ← ≤ 2 file change, no plan, builder + reviewer only
```

## Nano mode (≤ 2 file changes)

If `mode = nano`, run this short-circuit flow instead of the full pipeline. All stages below are skipped.

**Step 1 — Ask for the task:**
```
Nano mode active. Describe the change in one sentence:
(Builder will implement directly with no plan. Scope: ≤ 2 files.)
```
Wait for user description. Store as `NANO_TASK`.

**Step 2 — Spawn builder:**
```
Nano task: [NANO_TASK]

Make only the changes needed. Touch at most 2 files.
If the fix requires touching more than 2 files, STOP immediately and report:
  "Scope too large for nano — recommend upgrading to /pathly flow [feature] lite"
Do not create any plan files.
Verify with the project's standard verify command when done.
Report: files changed, verify result.
```

**Step 3 — Scope check:**

After builder completes, run:
```powershell
git diff --name-only HEAD
```
Count the files changed (excluding `plans/`). If the count is > 2 and builder did not already escalate:
- Ask the user:
  ```
  [NANO ESCALATION] Builder touched N files (nano limit is 2).
  [1] Accept — proceed with review as-is
  [2] Upgrade — restart as /pathly flow [feature] lite
  [3] Cancel
  ```
- Wait for reply. On [2]: stop and instruct user to rerun. On [3]: stop.

**Step 4 — Spawn reviewer:**
```
Review the nano change for [feature].
Run: git diff HEAD (or git diff --staged if not yet committed).
Check for correctness, obvious bugs, and rule violations.
Report: PASS or list each violation with file + line.
Do not write feedback files — report violations inline.
```

**Step 5 — Fix cycle (max 1):**

If reviewer reports violations:
- Spawn builder with the violation list. One fix pass only.
- If violations remain after 1 pass: stop and report. Recommend upgrading to lite for a full review loop.

If reviewer reports PASS — print:
```
[Nano complete] [feature] done.
Files changed: [list from git diff]
```
Exit. Do not run test or retro stages.

---

## Core rules

- Spawn the right subagent for each stage — never execute work yourself.
- Treat `/pathly flow` as a deterministic filesystem FSM. Before each action:
  read disk, recover state, process one event, and emit one next action.
- Store workflow checkpoints in `plans/$FEATURE/STATE.json` and append events
  to `plans/$FEATURE/EVENTS.jsonl` using `orchestrator/eventlog.py`.
  In `strict` rigor, these files are required before any agent spawns.
- Rigor controls process depth:
  - `lite`: 4 plan files, fewer gates, review/test can be final-only when risk is low.
  - `standard`: current 8-file pipeline with review after every conversation.
  - `strict`: 8 files plus mandatory `STATE.json`, `EVENTS.jsonl`, human approvals, review, and test gates.
- Default: pause at every stage transition, require human acknowledgement.
- Auto mode: skip pauses, run to completion.
- In `standard` and `strict`, reviewer runs after every implemented conversation.
- In `lite`, reviewer may run final-only unless feedback, touched files, or user preference requires earlier review.
- After every agent completes, check for feedback files before advancing.
- Max 2 feedback cycles per conversation and feedback file. If exceeded, stop and report.
- If a stage fails, report the failure and manual recovery command. Do not retry.
- Canonical FSM reference: `docs/ORCHESTRATOR_FSM.md`.

## FSM checkpoint protocol

The orchestrator (LLM) must consult `orchestrator/` at three specific points.

### 1. Startup recovery + integrity check

When `/pathly flow` starts or resumes, recover state in this order:

1. **Read STATE.json** — load `plans/<feature>/STATE.json` using `State` (`orchestrator/state.py`). If the file exists and parses cleanly, use that state.
2. **Fall back to EVENTS.jsonl replay** — if STATE.json is absent or unreadable, instantiate `EventLog(feature=FEATURE)` (`orchestrator/eventlog.py`) and call `log.reconstruct_state()`. Use the resulting state.
3. **Fall back to IDLE** — if neither file exists, start from `State()` (default IDLE). In `lite` and `standard` rigor this is not an error. In `strict` rigor: stop and report "STATE.json and EVENTS.jsonl not found — cannot recover state in strict mode."

**Disk feedback wins:** After loading state, scan `plans/<feature>/feedback/` for open feedback files. If any exist and STATE.json says the pipeline is not blocked, correct the in-memory state by calling `reduce(state, FileCreatedEvent(file=highest_priority_file))` and updating logs. Disk always wins over cached STATE.json.

**Log the outcome:** Print one of:
- `[FSM] State recovered from STATE.json: <state_name>`
- `[FSM] State reconstructed from EVENTS.jsonl: <state_name> (N events)`
- `[FSM] No prior state found — starting from IDLE`
- `[FSM] State corrected by disk feedback: <old_state> → <new_state>`

**Startup integrity check (runs immediately after state recovery, before any agent spawns):**

Check for two categories of problems:

*Safe issues* (orphan/expired feedback files — can be auto-resolved):
- Read frontmatter from each `plans/<feature>/feedback/*.md` file.
- If `created_by_event` is set and not found in `EVENTS.jsonl` → orphan.
- If `created_at + ttl_hours` has elapsed → expired.

*Real issues* (require human judgment):
- STATE.json says `BUILDING` but no conversation is marked `in_progress` in PROGRESS.md → FSM drift.

**Behavior by mode:**

| Situation | Normal (interactive) | Fast |
|---|---|---|
| Safe issues only | Show each file + reason, ask "delete and continue? [yes/no]" | Delete silently, log `[FSM AUTO] Removed orphan: <file>` |
| Real issues only | Show issue + suggestion, ask "continue anyway? [yes/no]" | Print issues, suggest `/pathly doctor`, stop |
| Both | Handle safe first, then ask about real issues | Delete safe, stop on real |
| No issues | Proceed silently | Proceed silently |

### 2. Before each agent spawn

Before spawning any subagent, execute this sequence:

1. **Choose the correct event** for the transition (e.g. `CommandEvent`, `AgentDoneEvent`, `FileCreatedEvent` — all from `orchestrator/events.py`).
2. **Compute new state** — call `reduce(state, event)` from `orchestrator/reducer.py`. This is a pure function; it never has side effects.
3. **Persist the transition** — call `log.append(event)` and `log.write_state_json(new_state)` on the `EventLog` instance (`orchestrator/eventlog.py`). Both must succeed before spawning.
4. **Spawn** the subagent.

Always update `new_state` after the call so subsequent decisions use the current state.

### 3. Backward compatibility

- If `plans/<feature>/` does not exist yet, create the directory before writing STATE.json or EVENTS.jsonl.
- If any IO operation fails (disk full, permission error, etc.), log a warning — `[FSM WARNING] Could not persist state: <error>` — and proceed with the spawn. Do not block the pipeline on logging failures.
- Missing STATE.json or EVENTS.jsonl is **not an error** in `lite` or `standard` rigor. Only `strict` rigor requires these files before any agent spawn.

## FSM guards

Run these three guards in order before any forward advance in the pipeline. All three must pass before spawning the next agent or moving to the next stage.

### Guard 1 — Feedback-open check

1. Scan `plans/<feature>/feedback/` for open files.
2. If any feedback files exist:
   - Identify the highest-priority file using the priority order: `HUMAN_QUESTIONS.md`, `ARCH_FEEDBACK.md`, `DESIGN_QUESTIONS.md`, `IMPL_QUESTIONS.md`, `REVIEW_FAILURES.md`, `TEST_FAILURES.md`.
   - Call `reduce(state, FileCreatedEvent(file=highest_priority_file))` (from `orchestrator/events.py` and `orchestrator/reducer.py`), then update logs with `log.append(event)` and `log.write_state_json(new_state)`.
   - Route to the responsible agent per the priority order already defined in the "Feedback file locations" section.
3. When that agent resolves and deletes the file:
   - Call `reduce(state, FileDeletedEvent(file))` (from `orchestrator/events.py`), update logs.
   - Re-scan `plans/<feature>/feedback/` for remaining open files.
4. Only advance (proceed to Guard 2) when no feedback files remain.

### Guard 2 — Retry-count check

Run this check before routing any feedback file to its responsible agent (after Guard 1 identifies the file):

1. Check `state.retry_count_by_key["conv-N:FILE.md"]` (from `orchestrator/state.py`), where `N` is the current conversation number and `FILE.md` is the feedback filename.
2. If the value is `> 2`:
   - Do not spawn the fix agent.
   - Write `plans/<feature>/feedback/HUMAN_QUESTIONS.md` with an escalation message identifying the conversation, the file, and the retry count.
   - Call `reduce(state, FileCreatedEvent("HUMAN_QUESTIONS.md"))`, update logs.
   - Stop and report: `"Retry limit exceeded for conv-N:FILE.md. Escalated to HUMAN_QUESTIONS.md."`
3. If the value is ≤ 2:
   - After routing the fix agent (spawning it), call `reduce(state, SystemEvent(action="RETRY", retry_key="conv-N:FILE.md"))` (from `orchestrator/events.py`), update logs so the retry counter increments.

**Exception:** `IMPL_QUESTIONS.md` and `DESIGN_QUESTIONS.md` are exempt — they are clarification requests, not fix loops. Do not check or increment `retry_count_by_key` for these two files.

### Guard 3 — Zero-diff stall check

Applies only after the builder finishes a `REVIEW_FAILURES.md` fix, before re-spawning the reviewer:

1. Run:
   ```bash
   git diff HEAD -- . ":(exclude)plans/"
   ```
2. If the command fails (not a git repo or git is unavailable): skip this check, log `[FSM WARNING] git diff failed — skipping zero-diff check`, and proceed to re-spawn reviewer.
3. If the output is empty (builder made no implementation changes):
   - Call `reduce(state, NoDiffDetectedEvent())` (from `orchestrator/events.py`), update logs.
   - Write `plans/<feature>/feedback/HUMAN_QUESTIONS.md` with a `[STALL]` tag:
     ```
     [STALL] Conversation N — builder and reviewer in zero-diff loop.
     Builder claimed to fix REVIEW_FAILURES.md but no code changed.
     Human decision required: accept as-is, override the rule, or rewrite the conversation scope.
     ```
   - Stop and report: `"Zero-diff loop detected for Conv N. Escalated to HUMAN_QUESTIONS.md."`
4. If the output is non-empty: proceed to re-spawn reviewer.

## Rigor escalator

The pipeline **always starts with the 4 core lite files** — no exceptions:

```
USER_STORIES.md
IMPLEMENTATION_PLAN.md
PROGRESS.md
CONVERSATION_PROMPTS.md
```

The escalator runs **after planning completes and before the first builder spawn**.
It looks at what the planner and architect discovered, then offers to add specific
extra files based on what the task actually needs. Nothing is added silently.

Default rigor when the user doesn't specify: **`lite`** (4 files only).

---

### Signal → file mapping

Each additional file has exactly one trigger signal. Check these after planning:

| Extra file | Trigger signal | How to detect |
|---|---|---|
| `ARCHITECTURE_PROPOSAL.md` | Cross-layer dependency found | Architect or planner mentions > 1 layer, or STORM_SEED.md references multiple layers |
| `EDGE_CASES.md` | High-risk keyword in a risk context | See rule below |
| `HAPPY_FLOW.md` | > 3 conversations planned | CONVERSATION_PROMPTS.md has more than 3 conversation blocks |
| `FLOW_DIAGRAM.md` | Long discovery path | STORM_SEED.md or scout/pathly explore output references > 3 files, or architect drew a multi-component diagram |

A file is only recommended if its signal fires. Files with no signal are not offered.

**EDGE_CASES.md keyword rule — context-aware detection:**

Scan USER_STORIES.md and STORM_SEED.md for these high-risk keywords:
`auth`, `payment`, `migration`, `security`, `schema`, `breaking change`

A keyword fires the signal **only** if it appears in a risk context. A risk context is:
- The keyword appears in the same sentence or bullet as a risk indicator:
  `fail`, `invalid`, `expire`, `breach`, `error`, `corrupt`, `race`, `concurrent`, `collision`, `rollback`, `sensitive`, `lost`, `overwrite`, `unauthorized`
- OR the keyword appears in a section or bullet heading that describes failure modes, edge cases, or error handling (e.g., "Error handling:", "Edge cases:", "What if...", "Failure scenario:")
- OR the keyword appears more than once across the document (repeated mention signals the author treats it as a load-bearing concern)

A keyword does **not** fire the signal if it appears only in a UI/label context — for example: "auth button label", "payment icon color", "update schema name in the sidebar". Pure naming and labeling mentions are ignored.

---

### Escalation offer (interactive mode)

If any signal fires, write `plans/<feature>/feedback/HUMAN_QUESTIONS.md`
before spawning the first builder:

```
[RIGOR ESCALATOR] — recommended additions for <feature>

The 4 core plan files are ready. Based on what was found during planning,
these additional files are recommended:

  ✦ ARCHITECTURE_PROPOSAL.md   → cross-layer dependencies detected
  ✦ EDGE_CASES.md              → keyword "payment" found in USER_STORIES.md
  ─ HAPPY_FLOW.md              → no signal (2 conversations planned)
  ─ FLOW_DIAGRAM.md            → no signal (discovery path was short)

Add to plan:
  [1] All recommended (ARCHITECTURE_PROPOSAL + EDGE_CASES)
  [2] ARCHITECTURE_PROPOSAL.md only
  [3] EDGE_CASES.md only
  [4] None — keep 4 core files only

Reply with 1, 2, 3, or 4:
```

Wait for user reply. Then:
- Spawn the **planner** to generate only the selected file(s), appending to the existing plan.
- Delete `HUMAN_QUESTIONS.md`.
- Continue to build.

If **no signals fire**: skip the offer entirely. Keep 4 core files. Proceed to build.

---

### Fast / auto mode behavior

In `fast` mode (or when `autoFlow = true`): skip the question.
Automatically apply **all recommended files** (all signals that fired) and continue.
Print: `[RIGOR AUTO] Adding: <file1>, <file2> — signals detected during planning.`

---

### Rules

- The 4 core files are **never removed**, never conditional, never skipped.
- Extra files are **additive only** — they extend the plan, never replace core files.
- Do not suggest downgrading. Only upward additions are offered.
- Do not add a file when its signal did not fire, even if the user asks for "standard".
  (If the user wants all 8 files explicitly, they should run `/pathly flow <feature> standard`.)
- Each file offered must show its triggering signal clearly — no silent additions.

## Health checks before skipping stages

Run these before jumping to the entry stage. Fail fast with a clear error.

**plan:**
- No pre-requisite check needed. Feature name is enough.
- Print: `[SKIPPED] Stage 0 (discovery) → entering at plan`

**build:**
- Check `plans/$FEATURE/` exists. If not: stop → `plans/$FEATURE/ not found. Run /pathly flow $FEATURE first to create the plan.`
- If `rigor = lite`, check the 4 required plan files exist: USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, CONVERSATION_PROMPTS.md.
- If `rigor = standard` or `strict`, check all 8 plan files exist: USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, CONVERSATION_PROMPTS.md, HAPPY_FLOW.md, EDGE_CASES.md, ARCHITECTURE_PROPOSAL.md, FLOW_DIAGRAM.md. If any missing: stop → list the missing files.
- If `rigor = strict`, also require STATE.json and EVENTS.jsonl.
- Read PROGRESS.md — resume from last TODO conversation (do not clear or restart).
- Print: `[SKIPPED] Discovery + plan → entering at build`
- Print: `Resuming from: Conversation N (last TODO in PROGRESS.md)`

**test:**
- Check `plans/$FEATURE/` exists with required files for the selected rigor (same as build).
- Check PROGRESS.md — all conversations must be DONE. If any TODO: stop → `Not all conversations are complete. Run /pathly flow $FEATURE build first.`
- Print: `[SKIPPED] Discovery + plan + implementation → entering at test`

## Feedback file locations

All feedback files live in `plans/[feature]/feedback/`.
A file existing = issue open. A file absent or deleted = resolved.

| File | Written by | Resolved by |
|---|---|---|
| `ARCH_FEEDBACK.md` | reviewer | architect |
| `REVIEW_FAILURES.md` | reviewer | builder |
| `TEST_FAILURES.md` | tester | builder |
| `IMPL_QUESTIONS.md` | builder `[REQ]` | planner (what should this do?) |
| `DESIGN_QUESTIONS.md` | builder `[ARCH]` | architect (how is this technically possible?) |
| `HUMAN_QUESTIONS.md` | any agent | user — pipeline enters `BLOCKED_ON_HUMAN` |

If multiple feedback files exist, route one at a time in this priority order:
`HUMAN_QUESTIONS.md`, `ARCH_FEEDBACK.md`, `DESIGN_QUESTIONS.md`,
`IMPL_QUESTIONS.md`, `REVIEW_FAILURES.md`, `TEST_FAILURES.md`.

## Subagent map

| Action | Spawn | Why |
|---|---|---|
| Storm | `architect` | technical exploration, opus |
| Explore codebase | `scout` | map existing code before planning |
| Plan | `planner` | user stories + decomposition |
| Implement | `builder` | code execution, scoped to one conversation |
| Review | `reviewer` | adversarial check after each conversation |
| Fix arch issue | `architect` | redesign before builder can continue |
| Fix impl issue | `builder` | targeted fix of review violations |
| Clarify requirement | `planner` | unblock builder on ambiguous spec |
| Test | `tester` | verify acceptance criteria |
| Fix test failure | `builder` | address failing criteria |
| Retro | `quick` | fast retrospective summary; retro skill/orchestrator writes files |

---

## Stage 0 — Discovery Path
*(skip if entryStage = plan, build, or test)*

If skipping: print the health check output from above and jump to the correct stage.

If running: print exactly this and wait for user input:

```
═══════════════════════════════════════════
  [feature-name] — Choose discovery path
═══════════════════════════════════════════

  [1] Quick storm
      Architect explores the idea now (~10 min)
      Best for: rough idea that needs shaping,
                technical unknowns to surface

  [2] Skip discovery
      Go straight to planning
      Best for: you already know what to build,
                small or familiar feature

  [3] Import PRD
      You have a requirements file ready
      Best for: BMAD output, hand-written PRD,
                any structured requirements doc

  [4] Explore first
      Explorer maps the codebase, then you decide
      Best for: unfamiliar code, "where does this go?",
                checking if something already exists

  [5] Full discovery
      PO discussion → Architect storm → Planner
      Best for: new features, unclear requirements,
                high stakeholder alignment needed

Reply with 1, 2, 3, 4, or 5:
```

**On '1'** → proceed to Stage 1 (Storm), then Stage 2 (Plan)

**On '2'** → skip Stage 1, go straight to Stage 2 (Plan)
  - Print: `Skipping discovery. Starting planning...`

**On '3'** → ask:
  ```
  Path to your PRD file? (e.g. docs/feature-prd.md)
  ```
  Wait for path input. Then run `/pathly prd-import [feature] [path] [rigor]`.

  After import, print:
  ```
  PRD imported. Plan files ready in plans/[feature]/

  The PRD covers your requirements. How do you want to proceed?
    [A] Skip to build — PRD is sufficient, go straight to implementation
    [B] PO gap-review — PO advisor reads the PRD and asks only about gaps
    [C] Architect storm — go to technical design before building

  Reply with A, B, or C:
  ```
  Wait for reply.

  - **A** → Skip Stage 1 and Stage 2. Jump directly to Stage 3 (Implement).
    Print: `Skipping discovery. Starting implementation from PRD plan.`

  - **B** → Emit `STATE_TRANSITION(to=PO_DISCUSSING)`, update logs. **Spawn** `po`:
    ```
    Run PO mode for the feature: [feature name]
    A PRD has already been imported. Read plans/[feature]/USER_STORIES.md as the baseline.
    Focus only on gaps: missing edge cases, unclear acceptance criteria, unstated constraints.
    The user will type "stop notes" when satisfied to write plans/[feature]/PO_NOTES.md.
    Remind them of this at the start.
    ```
    After PO agent completes, emit `STATE_TRANSITION(to=PO_PAUSED)`, update logs.
    Then proceed to Stage 3 (Implement). Skip Stage 1 (Storm) and Stage 2 (Plan) — plan files already exist.

  - **C** → Skip Stage 2 (prd-import already generated plan files). Proceed to Stage 1 (Storm).
    Print: `Plan files ready. Starting architect storm for technical design.`
    Spawn `architect` as per Stage 1.

**On '4'** → run a codebase exploration, then let the user choose their next step:

  **Spawn** `scout`:
  ```
  Explore the codebase for the feature: [feature name]
  Map where this functionality would live — layers, existing files, dependencies, anything already present.
  Output a short summary: relevant files found, likely touch points, open questions.
  Do not plan or implement — explore only.
  ```

  After scout completes, print:
  ```
  [Explore complete] Scout mapped the codebase.

  What next?
    [A] Plan — go to Stage 2 (planner uses scout findings as context)
    [B] Implement directly — nano mode, no plan (best if explore showed ≤ 2 files to touch)
    [C] Stop here — I'll review the explore output first

  Reply with A, B, or C:
  ```
  Wait for user reply.
  - **A** → set `exploreContext = scout output`. Proceed to Stage 2 (Plan). Planner will use scout findings.
  - **B** → switch to `mode = nano`. Skip Stage 2. Jump to nano mode flow (builder + reviewer only).
  - **C** → stop. Print: `Pipeline paused after explore. Resume with /pathly flow [feature] build when ready.`

---

**On '5'** → run three-phase full discovery (PO → Architect → Planner):

  Emit `STATE_TRANSITION(to=PO_DISCUSSING)`, update logs.

  **Phase 1 — PO Discussion:**

  **Spawn** `po`:
  ```
  Run PO mode for the feature: [feature name]
  Probe requirements interactively — problem, users, MVP scope, out-of-scope, constraints, edge cases.
  The user will type "stop notes" when satisfied to write plans/[feature]/PO_NOTES.md.
  Remind them of this at the start.
  ```

  After PO agent completes — emit `STATE_TRANSITION(to=PO_PAUSED)`, update logs.

  If not autoFlow — **PAUSE:**
  ```
  [Phase 1 — PO Discussion complete]
  Requirements captured in plans/[feature]/PO_NOTES.md.
  Ready for architect storm? Reply 'yes' to continue, or 'no' to stop here.
  ```
  - Proceed signal: call `reduce(state, HumanResponseEvent(value=reply))`, update logs, advance.
  - Stop signal: call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, halt.

  If autoFlow: record `HumanResponseEvent(value="auto-advance")`, update logs.

  **Phase 2 — Architect Storm:**

  **Spawn** `architect`:
  ```
  Run /pathly storm for the feature: [feature name]
  Context from PO discussion is in plans/[feature]/PO_NOTES.md — read it first.
  Explore the idea technically — layers, dependencies, design decisions.
  When the user is satisfied, they will type /stop plan to write STORM_SEED.md.
  Remind them of this at the start.
  ```

  If not autoFlow — **PAUSE:**
  ```
  [Phase 2 — Architect Storm complete]
  STORM_SEED.md written. Ready to plan? Reply 'yes' to continue, or 'no' to stop here.
  ```
  Wait for reply. On 'no': stop.

  **Phase 3 — Plan:**

  **Spawn** `planner`:
  ```
  Run /pathly plan [feature name] [rigor].
  Context from PO discussion is in plans/[feature]/PO_NOTES.md — read it first.
  If plans/STORM_SEED.md exists, consume it as pre-filled answers.
  Ensure every story references which phase/conversation delivers it.
  Ensure every phase references which stories it fulfills.
  After creating the selected rigor's plan files, list them as a summary.
  ```

  Skip Stage 1 and Stage 2 (already completed above). Proceed directly to Stage 3 (Implement).

---

## Stage 1 — Storm
*(only runs if user chose path 1)*

**Spawn** `architect`:
```
Run /pathly storm for the feature: [feature name]
Explore the idea technically — layers, dependencies, design decisions.
When the user is satisfied, they will type /stop plan to write STORM_SEED.md.
Remind them of this at the start.
```

If not autoFlow — **PAUSE:**
```
[Stage 1 — Storm complete]
STORM_SEED.md written (or skipped).
Ready to plan? Reply 'yes' to continue, or 'no' to stop here.
```
After user replies:
- If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))` (from `orchestrator/events.py` and `orchestrator/reducer.py`), update logs with `log.append(event)` and `log.write_state_json(new_state)`, then advance.
- If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
- If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

On 'no': stop.

---

## Stage 2 — Plan
*(only runs if user chose path 1 or 2)*

**Spawn** `planner`:
```
Run /pathly plan [feature name] [rigor].
If plans/STORM_SEED.md exists, consume it as pre-filled answers.
Ensure every story references which phase/conversation delivers it.
Ensure every phase references which stories it fulfills.
After creating the selected rigor's plan files, list them as a summary.
```

If not autoFlow — **PAUSE:**
```
[Stage 2 — Plan complete]
plans/[feature]/ created with the selected rigor's required files.
Review USER_STORIES.md and CONVERSATION_PROMPTS.md.
Reply 'go' to start implementation, or 'stop' to pause here.
```
After user replies:
- If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))`, update logs, then advance.
- If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
- If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

On 'stop': exit.

---

## Stage 3 — Implement + Review Loop

Read `plans/[feature]/PROGRESS.md`.
Track `retryCount = 0` per conversation.

While any conversation row has status TODO:

  **3a. Builder implements**

  **Spawn** `builder`:
  ```
  Run /pathly continue [feature] in manual mode.
  Execute conversation N only. Verify, update PROGRESS.md.
  If you hit requirement ambiguity (what should this do?): write plans/[feature]/feedback/IMPL_QUESTIONS.md
  If you hit a technical blocker (how is this possible?): write plans/[feature]/feedback/DESIGN_QUESTIONS.md
  Use formats from ~/.claude/FEEDBACK_PROTOCOL.md, then report blocked.
  Report: files changed, verify result, stories delivered.
  ```

  After builder completes — check for feedback files:

  → If `IMPL_QUESTIONS.md` exists (contains [REQ] tagged questions):
    **Spawn** `planner`:
    ```
    Read plans/[feature]/feedback/IMPL_QUESTIONS.md.
    Answer each [REQ] question — clarify in USER_STORIES.md or CONVERSATION_PROMPTS.md.
    Delete plans/[feature]/feedback/IMPL_QUESTIONS.md when resolved.
    ```

  → If `DESIGN_QUESTIONS.md` exists (contains [ARCH] tagged questions):
    **Spawn** `architect`:
    ```
    Read plans/[feature]/feedback/DESIGN_QUESTIONS.md.
    Resolve each [ARCH] question — update ARCHITECTURE_PROPOSAL.md with the approach, or IMPLEMENTATION_PLAN.md if this is a lite plan without ARCHITECTURE_PROPOSAL.md.
    Delete plans/[feature]/feedback/DESIGN_QUESTIONS.md when resolved.
    ```

  Both files can exist at the same time. Route one agent at a time using the FSM priority order.
  After both resolve → builder re-implements (do not increment retryCount for these).

  **3b. Reviewer checks**

  If `rigor = lite`, reviewer may run once after the final builder conversation unless feedback files, risky touched files, or user preference require per-conversation review.

  If `rigor = standard` or `strict`, reviewer runs after every builder conversation.

  If review is required for this point in the selected rigor, **spawn** `reviewer`:
  ```
  Review the changes from conversation N of [feature].
  Run: git diff HEAD~1 HEAD (or git diff --staged if not yet committed).
  Check against plans/[feature]/ARCHITECTURE_PROPOSAL.md and any rules in .claude/rules/ if present.
  If architectural violations found: write plans/[feature]/feedback/ARCH_FEEDBACK.md
  If implementation violations found: write plans/[feature]/feedback/REVIEW_FAILURES.md
  Use formats from ~/.claude/FEEDBACK_PROTOCOL.md.
  If all clear: report PASS.
  ```

  If lite skips review for this conversation, continue to **3c. Advance** after checking feedback files.

  After reviewer completes — check feedback files:

  → If `ARCH_FEEDBACK.md` exists:
    Increment retryCount. If retryCount > 2: STOP — report "Feedback loop exceeded for Conv N. Manual intervention required."

    **Spawn** `architect`:
    ```
    Read plans/[feature]/feedback/ARCH_FEEDBACK.md.
    Redesign the affected architecture in plans/[feature]/ARCHITECTURE_PROPOSAL.md, or plans/[feature]/IMPLEMENTATION_PLAN.md for lite plans without ARCHITECTURE_PROPOSAL.md.
    If phases need to change, update plans/[feature]/IMPLEMENTATION_PLAN.md.
    Delete plans/[feature]/feedback/ARCH_FEEDBACK.md when resolved.
    Report: what changed in the design.
    ```
    After architect resolves → go back to 3a (builder re-implements Conv N).

  → If `REVIEW_FAILURES.md` exists:
    Increment retryCount. If retryCount > 2: STOP — report "Feedback loop exceeded for Conv N. Manual intervention required."

    **Spawn** `builder`:
    ```
    Read plans/[feature]/feedback/REVIEW_FAILURES.md.
    Fix each violation listed. Do not change anything outside the listed violations.
    Delete plans/[feature]/feedback/REVIEW_FAILURES.md when all fixed.
    ```

    After builder completes — **zero-diff check** before re-spawning reviewer:
    ```bash
    git diff HEAD -- . ":(exclude)plans/" 2>/dev/null
    ```
    If the diff is empty (builder made no implementation changes):
    - Write `plans/[feature]/feedback/HUMAN_QUESTIONS.md`:
      ```
      [STALL] Conversation N — builder and reviewer in zero-diff loop.
      Builder claimed to fix REVIEW_FAILURES.md but no code changed.
      Violations: [paste REVIEW_FAILURES.md content]
      Human decision required: accept as-is, override the rule, or rewrite the conversation scope.
      ```
    - STOP. Report: "Zero-diff loop detected for Conv N. Escalated to HUMAN_QUESTIONS.md — manual intervention required."

    If diff is non-empty → go back to 3b (reviewer re-checks).

  → If no feedback files: reviewer passed.

  **3c. Advance**

  If not autoFlow — **PAUSE:**
  ```
  [Stage 3 — Conversation N complete + reviewed]
  Reviewer: PASS. Commit your changes now.
  Reply 'continue' for the next conversation, or 'stop' to pause here.
  ```
  After user replies:
  - If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))`, update logs, then advance.
  - If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
  - If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

  If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

  On 'stop': exit.

  Reset retryCount = 0. Proceed to next TODO conversation.

---

## Stage 4 — Test + Fix Loop

**Pre-gate — all conversations must be DONE:**

1. Read `plans/<feature>/PROGRESS.md` and check every conversation row in the "Conversation Breakdown" table.
2. If any row has status other than `DONE`: stop and report:
   ```
   Not all conversations are complete. Run /pathly flow <feature> build first. Incomplete: Conv N
   ```
   (Replace `N` with the number(s) of the incomplete conversation(s).)
3. When all conversation rows are `DONE`:
   - Call `reduce(state, ImplementCompleteEvent())` (from `orchestrator/events.py` and `orchestrator/reducer.py`). The resulting state must be `TESTING`.
   - Update logs: call `log.append(event)` and `log.write_state_json(new_state)` on the `EventLog` instance (`orchestrator/eventlog.py`).
   - Then proceed to spawn tester below.

Track `testRetryCount = 0`.

**Spawn** `tester`:
```
Read plans/[feature]/USER_STORIES.md.
Run /test to verify each acceptance criterion.
For each criterion: PASS / FAIL / NOT COVERED.
If any FAIL or NOT COVERED: write plans/[feature]/feedback/TEST_FAILURES.md
using the format in ~/.claude/FEEDBACK_PROTOCOL.md.
```

In `lite`, testing may be limited to the verify commands and directly relevant checks from the plan.

In `standard`, tester verifies acceptance criteria before retro.

In `strict`, tester must map every acceptance criterion to PASS / FAIL / NOT COVERED and cannot proceed with NOT COVERED criteria.

After tester completes — check for `TEST_FAILURES.md`:

→ If `TEST_FAILURES.md` exists:
  Increment testRetryCount. If testRetryCount > 2: STOP — report "Test failures unresolved after 2 fix cycles. Manual intervention required."

  **Spawn** `builder`:
  ```
  Read plans/[feature]/feedback/TEST_FAILURES.md.
  Fix each failing or uncovered criterion.
  Delete plans/[feature]/feedback/TEST_FAILURES.md when resolved.
  ```
  After builder resolves → re-spawn tester (go back to start of Stage 4).

→ If no TEST_FAILURES.md: all criteria pass.

If not autoFlow — **PAUSE:**
```
[Stage 4 — Test complete]
All acceptance criteria: PASS.
Reply 'done' to proceed to retro.
```
After user replies:
- If reply is a proceed signal ('yes', 'go', 'continue', 'done', or a numeric choice): call `reduce(state, HumanResponseEvent(value=reply))`, update logs, then advance.
- If reply is a stop signal ('no', 'stop'): call `reduce(state, HumanResponseEvent(value="stop"))`, update logs, write `STATE.json` via `log.write_state_json(new_state)`, then halt.
- If reply is unrecognised: re-prompt without recording a `HUMAN_RESPONSE` event.

If autoFlow: record `HumanResponseEvent(value="auto-advance")` at this skipped pause, update logs.

---

## Stage 5 — Retro

**Spawn** `quick`:
```
Run /pathly retro [feature].
Ask the 3 retrospective questions and return the RETRO.md-ready summary.
Do not write files; quick is read-only. The retro skill/orchestrator writes RETRO.md.
```

Report:
```
[Stage 5 — Retro complete]
Pipeline complete. RETRO.md written to plans/[feature]/.
Lessons appended to LESSONS_CANDIDATE.md (if any were extracted).
Feature '[feature]' is DONE.

To promote lessons to active memory: /pathly lessons
```
