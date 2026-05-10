# pathly

This is the canonical, tool-agnostic Pathly behavior for the pathly workflow.
Adapter skills should load and follow this prompt instead of duplicating workflow logic.

# Pathly

Use this workflow as the canonical front door for Pathly.

This core router works in host-neutral route names. Adapters decide how a user
invokes those routes in their environment.

## Parse `$ARGUMENTS`

Trim `$ARGUMENTS` and inspect the first word case-insensitively.

## Routes

### `start`

Route to the director agent with no feature argument. The director will ask the
user for their intent and decide the appropriate flow.

Run the director behavior from `core/skills/go.md` with no pre-filled intent.

### `continue`

Route to the orchestrator. The orchestrator reads `plans/*/STATE.json` to find
the active feature (most recently modified STATE.json) and resumes from the
current pipeline position.

Instruct the orchestrator: read `plans/*/STATE.json` sorted by modification
time (most recent first), pick the active feature, and resume the pipeline at
the current stage.

### `end`

Route to the orchestrator to close the current feature.

Instruct the orchestrator:
1. Read `plans/*/STATE.json` (most recently modified) to identify the active feature.
2. Read `plans/$FEATURE/PROGRESS.md` to check for incomplete conversations.
3. If any conversations are incomplete (status TODO or IN_PROGRESS), warn the
   user and ask for explicit confirmation before proceeding:
   ```
   Warning: <N> conversation(s) are not yet complete.
   Close anyway and run retro? [yes / no]
   ```
   Stop if the user says no.
4. Check whether tests have been run (STATE.json phase = test or retro, or
   team-flow test entry has been executed):
   - If not yet tested: route to `team-flow <feature> test`, which runs tests
     and then triggers retro.
   - If already tested: route to `retro <feature>` directly.
5. After retro completes, RETRO.md is written and the feature is closed.

### `meet`

Run the meet workflow from `core/skills/meet.md` with no argument. The meet
skill already scans `plans/*/STATE.json` to find the active feature.

### `help`

Run the Pathly help behavior from `core/skills/help.md` with no argument. The
help skill already scans `plans/*/STATE.json` to find the active feature and
prints a context-aware menu.

### Anything else (backward-compatible fallback)

If the first word is not one of the five verbs above (`start`, `continue`,
`end`, `meet`, `help`), treat the full `$ARGUMENTS` text as plain-English
intent and route to the director behavior from `core/skills/go.md` with the
full text pre-filled as the user's intent. This preserves backward
compatibility with callers that pass free-form text.

## Response Rule

Before invoking the selected behavior, print a short summary:

```text
Pathly route: <start|continue|end|meet|help|director>
Reason: <one sentence>
```
