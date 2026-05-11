# Troubleshooting

Common stuck states and how to recover from them. Run `pathly doctor` or `/pathly doctor` first — it catches most issues automatically.

---

## Workflow is stuck in BLOCKED_ON_HUMAN but no HUMAN_QUESTIONS.md exists

**Symptom:** `STATE.json` shows `BLOCKED_ON_HUMAN`, but `plans/<feature>/feedback/HUMAN_QUESTIONS.md` is missing.

**Cause:** A previous session crashed or was killed after writing the state transition but before writing the feedback file, leaving `STATE.json` ahead of the filesystem.

**Fix:**
1. Run `verify-state` — it will detect the mismatch and recommend a corrective event.
2. If unavailable, delete `STATE.json` and re-run the orchestrator. The disk-recovery algorithm re-derives state from `PROGRESS.md` and the remaining feedback files.
3. Never manually edit `STATE.json` to a previous state — run recovery instead.

---

## STATE.json and PROGRESS.md disagree

**Symptom:** `STATE.json` says `BUILDING` but `PROGRESS.md` shows all conversations as DONE.

**Cause:** `EVENTS.jsonl` was not flushed after the last successful build, or `PROGRESS.md` was manually edited.

**Fix:**
1. Trust `PROGRESS.md` — it is the human-readable record of what actually completed.
2. Delete `STATE.json`. Recovery will derive `IMPLEMENT_PAUSED` (all conversations done, no test results) and prompt the next action.
3. Check `EVENTS.jsonl` — the last event shows where the session ended.

---

## Stale feedback file is blocking the pipeline

**Symptom:** A feedback file exists in `plans/<feature>/feedback/` but the issue it describes was already resolved (manually fixed, or the feature direction changed).

**Cause:** The owning agent resolved the issue but forgot to delete the file, or the file was written speculatively and never actioned.

**Fix:**
1. Read the feedback file and confirm the issue no longer applies.
2. If resolved: delete the file. The FSM will resume from the stacked state on the next orchestrator step.
3. If still open but stale-TTL: check the `created_at` frontmatter. Files older than `ttl_hours` can be flagged by `verify-state`.
4. Never delete a feedback file that contains an unresolved question — answer it first.

---

## Retry budget exhausted — orchestrator wrote HUMAN_QUESTIONS.md [STALL]

**Symptom:** `HUMAN_QUESTIONS.md` contains `[STALL]` and reports that a feedback file exceeded 2 retry cycles.

**Cause:** The builder or architect attempted to resolve a feedback file twice and the reviewer or tester rejected it both times, or the builder produced no diff on a `REVIEW_FAILURES.md` resolution.

**Fix:**
1. Read the stalled feedback file and `HUMAN_QUESTIONS.md` together — the orchestrator explains the loop.
2. Options:
   - **Redesign:** If the feedback is architectural, the original design may be unimplementable. Start a `meet` session with the architect to revisit.
   - **Descope:** If the failing requirement is out of scope for this conversation, remove it from `CONVERSATION_PROMPTS.md` and open a new feature for it.
   - **Override:** If the reviewer is too strict for the current rigor level, manually delete `REVIEW_FAILURES.md` and add a note to `PROGRESS.md`. Only do this for `lite` features where the finding is non-blocking.
3. Delete `HUMAN_QUESTIONS.md` after the decision is made to unblock the pipeline.

---

## Builder produced no diff after resolving a review failure

**Symptom:** `HUMAN_QUESTIONS.md` contains `[STALL: NO_DIFF]`.

**Cause:** The builder marked a `REVIEW_FAILURES.md` resolved but made no code changes. The FSM detected the empty diff and escalated.

**Common causes:**
- The builder fixed the issue in a previous conversation that the reviewer didn't re-check.
- The review failure describes a pattern the builder already addressed elsewhere.
- The builder misread the file path.

**Fix:**
1. Verify whether the code change actually exists (`git diff HEAD`).
2. If the fix is already in the code: delete `REVIEW_FAILURES.md` manually with a note confirming the fix location, then delete `HUMAN_QUESTIONS.md`.
3. If not fixed: reopen with the builder, providing the exact file and line the reviewer flagged.

---

## Lost track of which conversation is next

**Symptom:** `PROGRESS.md` exists but you are unsure which conversation to run next.

**Fix:**
1. Read `plans/<feature>/PROGRESS.md` — TODO conversations are listed explicitly.
2. Read `plans/<feature>/CONVERSATION_PROMPTS.md` — each conversation has a numbered header.
3. Run `/pathly build <feature>` — the build skill reads `PROGRESS.md` and picks the next TODO automatically.

---

## Feature plan files missing for an existing feature

**Symptom:** `plans/<feature>/` directory exists but some plan files are absent (e.g., `ARCHITECTURE_PROPOSAL.md` is missing for a `standard` feature).

**Cause:** Feature was started at `lite` rigor and escalated, but the escalator did not create the missing files yet.

**Fix:**
1. Run `verify-state` — it checks that required files exist for the current rigor level.
2. If files need to be created: spawn the architect or planner with explicit instructions to produce the missing file before the next build.
3. Do not start a build conversation while required plan files are absent — the builder will produce under-specified work.

---

## pathly-engine FSM and ORCHESTRATOR_FSM.md are out of sync

**Symptom:** A state name in `pathly-engine/orchestrator/` does not match the spec in `docs/ORCHESTRATOR_FSM.md`.

**Fix:**
1. Treat `docs/ORCHESTRATOR_FSM.md` as the source of truth for state names and transition rules.
2. Update the Python enum in `pathly-engine/orchestrator/` to match the spec.
3. Run the orchestrator test suite (`pytest pathly-engine/tests/`) to confirm no transitions broke.
4. If the spec itself is wrong, update the spec first, then the code, so the commit message explains the intent.
