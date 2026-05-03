# fsm-wiring — Edge Cases

## Category 1: State Recovery Failures

### EC-1.1: Corrupt STATE.json
- **Trigger**: `STATE.json` exists but contains invalid JSON (truncated file, partial write)
- **Current behavior**: Python `json.loads()` raises `JSONDecodeError`
- **Expected behavior**: Fall back to `EVENTS.jsonl` replay. If that also fails, start from `IDLE` and log a warning. Do not crash the pipeline.
- **Handled in**: Phase 1 → Conv 1 (recovery prose in `## FSM checkpoint protocol`)

### EC-1.2: STATE.json Contradicts Disk Feedback Files
- **Trigger**: `STATE.json` says `BUILDING` but `plans/<feature>/feedback/HUMAN_QUESTIONS.md` exists on disk
- **Current behavior**: FSM state and disk are out of sync (e.g. pipeline crashed mid-transition)
- **Expected behavior**: Disk wins. Correct state to `BLOCKED_ON_HUMAN`, log the correction: `State corrected: BUILDING → BLOCKED_ON_HUMAN (disk feedback files found).`
- **Handled in**: Phase 1 → Conv 1 (disk-wins rule in `## FSM checkpoint protocol`)

### EC-1.3: EVENTS.jsonl Contains Unknown Event Type
- **Trigger**: A future event type is added to the schema; old log is replayed on an older version
- **Current behavior**: `event_factory()` returns a base `Event` with unknown type; reducer returns state unchanged for unknown types
- **Expected behavior**: Skip the unknown line, log a warning, continue replay. Do not stop.
- **Handled in**: Phase 1 → Conv 1 (prose instructs to continue replay on unknown events)

---

## Category 2: Feedback File Conflicts

### EC-2.1: Multiple Feedback Files Open Simultaneously
- **Trigger**: Reviewer writes `ARCH_FEEDBACK.md`; architect fails to delete it; builder also writes `REVIEW_FAILURES.md`
- **Current behavior**: Both files exist; pipeline is confused about which to route
- **Expected behavior**: Priority order is enforced. Route `ARCH_FEEDBACK.md` first (architect). Do not touch `REVIEW_FAILURES.md` until `ARCH_FEEDBACK.md` is resolved.
- **Handled in**: Phase 2 → Conv 2 (Guard 1 re-scans after each resolution; priority order explicit)

### EC-2.2: Feedback File Deleted by Manual Cleanup
- **Trigger**: Operator manually deletes `REVIEW_FAILURES.md` without builder fixing anything
- **Current behavior**: Next scan sees no file; pipeline advances as if reviewer passed
- **Expected behavior**: This is acceptable — the operator explicitly cleared the block. The FSM sees `FILE_DELETED` on next scan and restores `previous_state`. Pipeline continues.
- **Handled in**: Phase 2 → Conv 2 (Guard 1 re-scan is file-presence-based, not agent-outcome-based)

### EC-2.3: IMPL_QUESTIONS.md and DESIGN_QUESTIONS.md Arrive Together
- **Trigger**: Builder writes both files in one pass (has both a requirements question and a technical question)
- **Current behavior**: Both files exist; only one agent can run at a time
- **Expected behavior**: Route `DESIGN_QUESTIONS.md` second in priority (after `ARCH_FEEDBACK.md`). Handle `IMPL_QUESTIONS.md` after. Neither file consumes retry budget. Retry counter not incremented for either.
- **Handled in**: Phase 2 → Conv 2 (Guard 2 exempts both from retry; Guard 1 handles one at a time)

---

## Category 3: Retry and Stall Loops

### EC-3.1: Retry Budget Exhausted
- **Trigger**: `state.retry_count_by_key["conv-2:REVIEW_FAILURES.md"]` reaches 3 (three separate REVIEW_FAILURES.md fix attempts for Conv 2)
- **Current behavior**: Pipeline spawns builder a fourth time
- **Expected behavior**: Before spawning, Guard 2 detects `> 2`. Write `HUMAN_QUESTIONS.md`. FSM transitions to `BLOCKED_ON_HUMAN`. Pipeline stops. Report: `Feedback loop exceeded for Conv 2 (REVIEW_FAILURES.md). Manual intervention required.`
- **Handled in**: Phase 2 → Conv 2 (Guard 2)

### EC-3.2: Zero-Diff Stall — Plan Files Changed But No Code Changed
- **Trigger**: Builder deletes `REVIEW_FAILURES.md` and modifies a plan file, but touches no implementation files. `git diff HEAD -- . ":(exclude)plans/"` returns empty.
- **Current behavior**: Reviewer re-runs; same violations found; loop continues
- **Expected behavior**: Guard 3 detects empty diff (plan-excluded). Write `HUMAN_QUESTIONS.md [STALL]`. Stop.
- **Handled in**: Phase 2 → Conv 2 (Guard 3 exclusion pattern `":(exclude)plans/"`)

### EC-3.3: git diff Fails (Not a Git Repo)
- **Trigger**: Project is not in a git repo; `git diff` exits with non-zero or raises
- **Current behavior**: Guard 3 crashes the pipeline
- **Expected behavior**: Skip the stall check. Log warning: `git diff failed — skipping zero-diff check`. Proceed to reviewer.
- **Handled in**: Phase 2 → Conv 2 (Guard 3 error-handling prose)

---

## Category 4: Pipeline Entry and Stage Skipping

### EC-4.1: Stage 4 Entry With Incomplete PROGRESS.md
- **Trigger**: User runs `/team-flow my-feature test` with Conv 2 still `TODO` in PROGRESS.md
- **Current behavior**: Tester spawns and tests incomplete implementation
- **Expected behavior**: Pre-gate reads PROGRESS.md. Detects incomplete conv. Stops: `Not all conversations are complete. Run /team-flow my-feature build first. Incomplete: Conv 2`. FSM does not transition to `TESTING`.
- **Handled in**: Phase 3 → Conv 3 (Stage 4 pre-gate)

### EC-4.2: First Run — plans/<feature>/ Directory Does Not Exist Yet
- **Trigger**: Brand-new feature; orchestrator tries to write `EVENTS.jsonl` before plan directory is created (early in Stage 0)
- **Current behavior**: `EventLog` raises `FileNotFoundError` if directory is missing
- **Expected behavior**: `EventLog.__init__` calls `os.makedirs(..., exist_ok=True)` — directory is created automatically. First event writes normally.
- **Handled in**: Phase 1 → Conv 1 (`EventLog` already handles this; SKILL.md prose documents the behaviour)

### EC-4.3: Strict Rigor — No STATE.json on Startup
- **Trigger**: `/team-flow my-feature strict` invoked; `STATE.json` does not exist
- **Current behavior**: Pipeline continues without FSM enforcement
- **Expected behavior**: Stop and report: `strict mode requires STATE.json. Run /team-flow <feature> build to initialize.` Do not spawn any agent.
- **Handled in**: Phase 1 → Conv 1 (recovery prose includes strict-rigor gate)

---

## Category 5: Human Interaction Edge Cases

### EC-5.1: Unrecognised Pause Reply
- **Trigger**: Operator types `maybe` at a pause prompt
- **Current behavior**: Skill may interpret this as 'yes' or 'no' depending on prose
- **Expected behavior**: Re-prompt without recording a `HUMAN_RESPONSE` event. `EVENTS.jsonl` is not polluted with ambiguous values.
- **Handled in**: Phase 3 → Conv 3 (human pause events prose)

### EC-5.2: Fast Mode — Pause Points Skipped
- **Trigger**: `/team-flow my-feature fast` — no human pause points
- **Current behavior**: Events log is missing all human responses
- **Expected behavior**: Record `HumanResponseEvent(value="auto-advance")` at each skipped pause. Log remains coherent and replayable.
- **Handled in**: Phase 3 → Conv 3 (fast mode auto-advance prose)

---

## Known Limitations

- Phase 2 wires the FSM into SKILL.md prose only. The orchestrator is an LLM and may miss a checkpoint if the context window is full or the prompt is misread. A future phase (Phase 4 per IMPLEMENTATION_PLAN_FSM.md) adds audit verification.
- `reconstruct_state()` replays all events from the beginning of `EVENTS.jsonl` — for very long pipelines this could be slow. Snapshotting is intentionally deferred.
- The retry budget (`> 2`) is hard-coded in SKILL.md prose. Making it configurable is out of scope for this plan.
