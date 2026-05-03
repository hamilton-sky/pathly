# Feedback File Protocol

Feedback files are how agents communicate problems back up the chain.
They live in `plans/<feature>/feedback/` and are **deleted when resolved**.

The orchestrator checks for feedback files after every stage.
If one exists → route to the responsible agent → wait for resolution → delete → continue.

---

## Feedback Files

### ARCH_FEEDBACK.md — reviewer or tester → architect

**Trigger:** Reviewer finds a structural/architectural violation. Layer dependency reversed,
wrong abstraction, design decision that must change before implementation can continue.

**Written by:** reviewer  
**Read and resolved by:** architect — updates ARCHITECTURE_PROPOSAL.md, then notifies orchestrator  
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
**Read and resolved by:** architect — updates ARCHITECTURE_PROPOSAL.md with a revised approach, then deletes file  
**Then:** builder re-reads ARCHITECTURE_PROPOSAL.md and continues with the new approach

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

## Resolution Rules

1. **Deleting the file = resolved.** The agent that fixes the issue deletes the
   feedback file when done. The orchestrator seeing no file means clear to proceed.

2. **Max 2 retry cycles per conversation.** If a feedback loop triggers more than
   twice for the same conversation, stop and report to the user. Infinite loops
   mean the plan itself is broken.

3. **Feedback is blocking.** The pipeline does not advance to the next conversation
   until all feedback files for the current conversation are resolved.

4. **ARCH_FEEDBACK blocks everything.** An architectural violation cannot be
   patched by the builder — it must be resolved by the architect before any
   further implementation happens.

---

## Escalation Paths (who talks to whom)

```
reviewer ──► ARCH_FEEDBACK.md    ──► architect ──► updates ARCHITECTURE_PROPOSAL.md
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

No other escalation paths exist. Agents do not communicate outside these defined channels.
