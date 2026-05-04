# Feedback File Protocol

Feedback files are how agents communicate problems back up the chain.
They live in `plans/<feature>/feedback/` and are **deleted when resolved**.

The orchestrator FSM checks for feedback files after every event.
If one exists, the FSM enters `BLOCKED_ON_FEEDBACK`, routes to the responsible
agent, waits for deletion, then returns to the previous logical state.

---

## Frontmatter (TTL / orphan detection)

Every feedback file carries a YAML frontmatter block injected automatically
by the `inject_feedback_ttl.py` PostToolUse hook:

```yaml
---
created_at: 2026-05-04T08:12:00Z
created_by_event: <last-event-timestamp-or-id>
ttl_hours: 24
---
```

**What these fields mean:**

| Field | Purpose |
|---|---|
| `created_at` | ISO-8601 UTC. Used to detect files that outlived their TTL. |
| `created_by_event` | Timestamp/ID of the last event in `EVENTS.jsonl` when the file was written. If this event no longer exists in the current log, the file is an orphan from a previous run. |
| `ttl_hours` | Hours after `created_at` at which the file is considered stale (default 24). |

**Invariant enforced by `/verify-state`:**
- `created_by_event` not found in `EVENTS.jsonl` → orphan → safe to delete
- `created_at + ttl_hours` has elapsed → stale → safe to delete

Agents do not need to write frontmatter manually — the hook handles it.
If the hook is not installed, feedback files work exactly as before (no TTL).

---

## Feedback Files

### ARCH_FEEDBACK.md — reviewer or tester → architect

**Trigger:** Reviewer finds a structural/architectural violation. Layer dependency reversed,
wrong abstraction, design decision that must change before implementation can continue.

**Written by:** reviewer  
**Read and resolved by:** architect — updates ARCHITECTURE_PROPOSAL.md, or IMPLEMENTATION_PLAN.md for lite plans, then notifies orchestrator  
**Then:** planner updates IMPLEMENTATION_PLAN.md if phases change → builder re-implements

```markdown
# Architectural Feedback — Conv N
## Issue
[what architectural rule was violated or what design decision is wrong]
## Affected
[file, phase, or layer — e.g. "Phase 2, glue layer, login_action.py"]
## Required Action
[what the architect needs to redesign]
## Raised by
reviewer / tester
```

---

### REVIEW_FAILURES.md — reviewer → builder

**Trigger:** Reviewer finds implementation-level bugs: wrong resolver injection,
raw CSS in glue layer, missing register(), logic in wrong layer — fixable without
changing the architecture.

**Written by:** reviewer  
**Read and resolved by:** builder — fixes the specific violations, then deletes file  
**Then:** reviewer re-checks the same conversation

```markdown
# Review Failures — Conv N
## Failures
- [ ] [file:line] [rule violated] — [what to fix]
- [ ] [file:line] [rule violated] — [what to fix]
## Raised by
reviewer
```

**`[AUTO_FIX]` findings (trivial, no human turn required):**

The reviewer may tag mechanically-unambiguous findings as `[AUTO_FIX]` with an inline patch.
The builder applies all `[AUTO_FIX]` patches in a single batch pass before handling regular violations.

```markdown
- [AUTO_FIX] [file:line] — [rule] — [description]
  patch: |
    <<<<<<< original
    [exact original line(s)]
    =======
    [exact replacement — empty for deletion]
    >>>>>>> fixed
```

**Builder auto-fix rules:**
1. Apply every `[AUTO_FIX]` patch exactly as written — no interpretation.
2. If a patch fails to apply (line not found / already changed), treat it as a regular violation.
3. After all `[AUTO_FIX]` patches are applied, handle any remaining regular violations normally.
4. Delete `REVIEW_FAILURES.md` only when all items (auto-fix and regular) are resolved.

---

### TEST_FAILURES.md — tester → builder

**Trigger:** Tester runs acceptance criteria and one or more FAIL or are NOT COVERED.

**Written by:** tester  
**Read and resolved by:** builder — fixes failing criteria, then deletes file  
**Then:** tester re-runs the affected criteria

```markdown
# Test Failures — [Feature]
## Failing Criteria
| Story | Criterion | Expected | Actual |
|-------|-----------|----------|--------|
| S1.1  | [text]    | [result] | [result] |
## Not Covered
- S2.1: [criterion text] — no test exists
## Raised by
tester
```

---

### IMPL_QUESTIONS.md — builder → planner

**Trigger:** Builder encounters a **requirement ambiguity** — the plan is unclear,
contradictory, or missing a decision about what the feature should do.

**Written by:** builder  
**Read and resolved by:** planner — clarifies in USER_STORIES.md or CONVERSATION_PROMPTS.md, then deletes file  
**Then:** builder resumes the blocked conversation

Each question must be tagged `[REQ]`. If a question is architectural ("how should this be built?"), it does not belong here — write it to DESIGN_QUESTIONS.md instead.

```markdown
# Implementation Questions — Conv N
## Questions
- [REQ] [what specific requirement decision is needed]
- [REQ] [what specific requirement decision is needed]
## Context
[what the builder tried, why it's ambiguous]
## Raised by
builder
```

---

### DESIGN_QUESTIONS.md — builder → architect

**Trigger:** Builder hits a **technical blocker** — the architecture says to do X,
but X is not possible given the framework, the site, or discovered constraints.
This is not a "what should this do?" question (that goes to planner) — it is a
"how is this technically possible?" question.

Examples:
- Plan says use role resolver, but the element has no role attribute on this site
- Architecture assumes a shared base class, but the framework doesn't support it
- A resolver strategy is specified that conflicts with how the page actually renders

**Written by:** builder  
**Read and resolved by:** architect — updates ARCHITECTURE_PROPOSAL.md with a revised approach, or IMPLEMENTATION_PLAN.md for lite plans, then deletes file  
**Then:** builder re-reads the updated design source and continues with the new approach

Each question must be tagged `[ARCH]`. If a question is about requirements ("what should this do?"), it does not belong here — write it to IMPL_QUESTIONS.md instead.

```markdown
# Design Questions — Conv N
## Questions
- [ARCH] [what the architecture specifies and why it doesn't work in practice]
- [ARCH] [the specific design decision needed]
## Constraint discovered
[what the builder found — e.g. "button has no role, only a data-testid"]
## Raised by
builder
```

---

---

### HUMAN_QUESTIONS.md — any agent → user

**Trigger — two cases:**

1. **`[STALL]` — zero-diff loop (auto-escalation):** Builder claimed to fix `REVIEW_FAILURES.md` but `git diff` shows no code changed. The orchestrator writes this file immediately without incrementing retryCount. Format:
   ```
   [STALL] Conversation N — builder and reviewer in zero-diff loop.
   Builder claimed to fix REVIEW_FAILURES.md but no code changed.
   Violations: <paste original REVIEW_FAILURES.md content>
   Human decision required: accept as-is, override the rule, or rewrite the conversation scope.
   ```

2. **`[BLOCKED]` — unresolvable by any agent:** A question requiring a human product or business decision outside the domain of planner, architect, or builder.
   Examples:
   - "Two acceptance criteria directly contradict each other — which takes priority?"
   - "The plan assumes X but the codebase shows Y — which is the source of truth?"

**Written by:** orchestrator (`[STALL]`) or any agent (`[BLOCKED]`)
**Resolved by:** user — answer directly in chat, then delete the file
**Effect:** pipeline enters `BLOCKED_ON_HUMAN` until the file is deleted.

---

## Resolution Rules

1. **Deleting the file = resolved.** The agent that fixes the issue deletes the
   feedback file when done. The orchestrator FSM seeing no file means the
   blocking event is resolved.

2. **Max 2 retry cycles per conversation and feedback file.** If a feedback loop
   triggers more than twice for the same retry key, stop and report to the user.
   Infinite loops mean the plan itself is broken.

3. **Zero-diff escalation (STALL).** If builder resolves `REVIEW_FAILURES.md` but
   `git diff` shows no implementation changes, the orchestrator immediately writes
   `HUMAN_QUESTIONS.md` with tag `[STALL]` and stops — without consuming a retry cycle.
   This catches loops where the builder acknowledges violations without actually fixing them.

3. **Feedback is blocking.** The pipeline does not advance to the next conversation
   until all feedback files for the current conversation are resolved.

4. **ARCH_FEEDBACK blocks everything.** An architectural violation cannot be
   patched by the builder — it must be resolved by the architect before any
   further implementation happens.

5. **Deterministic priority.** If multiple feedback files exist, route one at a
   time using the order in `docs/ORCHESTRATOR_FSM.md`.

---

## Escalation Paths (who talks to whom)

```
reviewer ──► ARCH_FEEDBACK.md    ──► architect ──► updates ARCHITECTURE_PROPOSAL.md or IMPLEMENTATION_PLAN.md
         └─► REVIEW_FAILURES.md  ──► builder   ──► fixes violations

tester   ──► TEST_FAILURES.md    ──► builder   ──► fixes failing criteria

builder  ──► IMPL_QUESTIONS.md   ──► planner   ──► clarifies requirement
         └─► DESIGN_QUESTIONS.md ──► architect ──► resolves technical blocker
```

**Rule:** Use IMPL_QUESTIONS for "what should this do?" Use DESIGN_QUESTIONS for "how is this technically possible?" They go to different agents for a reason. Sending a technical question to the planner wastes time — they can't answer it.

**Tag rule:** Every question in a feedback file must carry its tag:
- `[REQ]` → IMPL_QUESTIONS.md → planner
- `[ARCH]` → DESIGN_QUESTIONS.md → architect
- `[UNSURE]` → both files → let the correct owner discard it

If you have both types, write both files. If classification is genuinely unclear, use `[UNSURE]` and write to both — forced misclassification wastes more time than writing twice. Mixed files without tags will be routed incorrectly.

**Auto-classification hook:** The framework installs a `PostToolUse` hook (`~/.claude/hooks/classify_feedback.py`) that fires whenever `IMPL_QUESTIONS.md` is written. It reads each question, calls Haiku to classify, rewrites the file with tags, and auto-splits `[ARCH]` questions into `DESIGN_QUESTIONS.md`. If questions are already tagged the hook exits immediately. If `ANTHROPIC_API_KEY` is not set it exits silently — the pipeline continues unaffected.

No other escalation paths exist. Agents do not communicate outside these defined channels.
