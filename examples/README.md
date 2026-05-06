# Examples

Worked examples of complete pipeline runs. Each folder is the actual plan produced by `/team-flow` for a real feature, plus a `STORY.md` narrative that explains what happened.

## Current Example

### add-cost-meter/

A small feature built with **lite rigor**.
Shows: 4-file plan, short conversation breakdown, reviewer pass, and the normal
planner -> builder -> reviewer loop.

Read `add-cost-meter/STORY.md` first for context, then look at the plan files.

## Recommended Routing Examples

These are the three examples Pathly should document publicly because they show
the intended shape of the system without inflating the default workflow.

### 1. Small bug fix -> `nano`

Example request:

```text
/pathly fix checkout button label typo
```

Recommended route:

```text
director -> builder -> reviewer
```

Use `nano` when all are true:

- The change is clearly scoped.
- It should touch at most 1-2 files.
- No new user story decomposition is needed.
- No architecture or product-scope ambiguity exists.

What the example should show:

- No plan folder creation.
- Builder implements one small fix.
- Reviewer checks the diff.
- Feature exits quickly with low token and latency cost.

### 2. Medium feature -> `lite`

Example request:

```text
/pathly add saved filters to the orders page
```

Recommended route:

```text
director -> planner -> builder -> reviewer -> tester
```

Use `lite` when:

- The feature is real user-facing work.
- Stories and acceptance criteria need to be written down.
- The implementation can still stay compact.
- Risk is moderate and cross-layer design is straightforward.

Optional consultation:

- `po` only if the user problem, scope, or success criteria are unclear.
- `architect` only if risk signals appear during planning.

What the example should show:

- `USER_STORIES.md`, `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, and `CONVERSATION_PROMPTS.md`.
- Conversation decomposition with purpose and dependency per task.
- Tester verifies acceptance criteria at the end.

### 3. Risky change -> `standard` or `strict`

Example request:

```text
/pathly add password reset with token expiry and audit logging
```

Recommended route:

```text
director -> planner -> architect -> builder -> reviewer -> tester
```

Use `standard` or `strict` when:

- Security, auth, payments, migrations, compliance, or rollback matter.
- Shared contracts or multiple layers are affected.
- The planner cannot safely break work down without design decisions.

Optional consultation:

- `po` if acceptance criteria, user impact, or out-of-scope boundaries are unclear.

What the example should show:

- Architecture proposal and edge-case coverage.
- Explicit verification mapping.
- Risk, rollback, and approval notes.
- Clear reasons why architect was brought in.

## Recommendation

Keep the default workflow lean:

```text
nano   -> director -> builder -> reviewer
lite   -> director -> planner -> builder -> reviewer -> tester
strict -> director -> planner -> architect -> builder -> reviewer -> tester
```

Do not add a general-purpose "consult any agent" stage to every flow. If you
want that capability, make it an advanced helper for one bounded question to one
named role, not a normal pipeline step.

---

To run your own feature through the pipeline:

```text
/pathly flow my-feature-name
```