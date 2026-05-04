# Builder Delegation Plan

## Goal

Allow the builder to delegate small, focused research and verification tasks to
lightweight subagents so implementation quality improves without weakening the
framework's ownership, review, and feedback guarantees.

The core principle:

```text
Builder remains the single implementation owner.
Subagents may investigate, summarize, or verify.
Only builder edits feature code unless the plan explicitly splits ownership.
```

## Why This Matters

Builder often needs more context before making a safe change:

- existing component or API patterns
- related tests
- similar implementations
- dependency boundaries
- risky edge cases
- likely verification commands

Today builder must gather all of that itself. For larger or unfamiliar changes,
small read-only subagents can collect context in parallel, giving builder better
inputs before editing.

## Proposed Agent: Scout

Add a lightweight subagent role:

```yaml
name: scout
role: scout
model: haiku
skills: []
description: Focused read-only codebase investigator. Answers one narrow
question for builder and returns concise findings with file references.
```

Scout is not an implementer. Scout is a focused codebase lookup worker.

## Scout Can Do

- Read files.
- Search the codebase.
- Summarize existing patterns.
- Find usages of a component, function, API, or convention.
- Identify relevant tests.
- Compare two small implementation options.
- Report likely risks or missing context.
- Suggest verification commands.

## Scout Cannot Do

- Edit files.
- Commit changes.
- Modify plans or progress.
- Make architecture decisions.
- Resolve feedback files.
- Bypass reviewer, tester, or orchestrator gates.
- Spawn additional agents.

## Example Delegations

Good scout tasks:

```text
Scout 1: Find existing modal implementations and summarize the shared pattern.
Scout 2: Locate tests around checkout form validation.
Scout 3: Inspect how API errors are surfaced in the UI.
Scout 4: Find whether a helper already exists for currency formatting.
```

Bad scout tasks:

```text
Scout 1: Implement the modal.
Scout 2: Refactor the checkout page.
Scout 3: Decide the architecture.
Scout 4: Fix all failing tests.
```

## Builder Workflow

Builder should use scouts only when the extra context is useful.

Suggested flow:

1. Read the active conversation prompt.
2. Identify unknowns that can be answered independently.
3. Spawn one to three scout tasks.
4. Collect scout findings.
5. Decide implementation approach.
6. Edit files directly as builder.
7. Verify.
8. Update `PROGRESS.md`.
9. Let reviewer/tester gates run as normal.

## When Builder Should Delegate

Delegate when any are true:

- The relevant code path is unfamiliar.
- There are multiple likely implementation patterns.
- A reusable helper or component may already exist.
- Tests are spread across the repo.
- The change touches more than one layer.
- The builder needs quick confidence before editing.

Do not delegate when:

- The change is trivial and obvious.
- The cost of delegation exceeds the work.
- The task is high-risk and needs architect/planner input instead.
- The subtask would require editing overlapping files.

## Ownership Rules

Default rule:

```text
Scout output is advisory.
Builder owns the final implementation.
Reviewer owns correctness review.
Tester owns acceptance verification.
Orchestrator owns workflow state.
```

If future versions allow write-capable subagents, they must have disjoint file
ownership declared up front. Until then, scouts are read-only.

## Feedback Interaction

Scout findings should not create or resolve feedback files.

If a scout discovers ambiguity:

- requirement ambiguity -> builder writes `IMPL_QUESTIONS.md`
- architecture ambiguity -> builder writes `DESIGN_QUESTIONS.md`
- human decision needed -> builder writes `HUMAN_QUESTIONS.md`

The normal feedback protocol still owns routing.

## Prompt Contract

Builder should delegate with a narrow prompt:

```text
You are a read-only scout for the <feature> feature.

Question:
<one focused question>

Rules:
- Do not edit files.
- Do not modify plans or feedback files.
- Search only enough to answer this question.
- Return concise findings with file paths and relevant line references.
- If uncertain, say what is missing.
```

Scout response format:

```text
Findings:
- <fact> (<file>:<line>)
- <fact> (<file>:<line>)

Recommendation:
<short recommendation or "No recommendation">

Open Questions:
- <only if needed>
```

## Implementation Plan

### Phase 1: Documentation and Agent Contract

- Add `agents/scout.md`.
- Update `agents/README.md` role map.
- Update builder documentation to allow read-only scout delegation.
- Document that scouts are advisory and cannot edit.

### Phase 2: Builder Prompt Update

- Update `agents/builder.md` with delegation rules.
- Update `skills/build/SKILL.md` to describe when builder may use scouts.
- Add guardrails:
  - maximum three scout tasks per conversation by default
  - scouts must be read-only
  - builder must summarize scout findings before editing

### Phase 3: Orchestrator Awareness

- Keep orchestrator single-owner by default.
- Do not make scouts FSM stages.
- Treat scout calls as builder-internal context gathering.
- Optionally log scout usage in `AgentDoneEvent.metadata` later for cost and
  audit visibility.

### Phase 4: Tests

Add static tests that verify:

- `agents/scout.md` forbids editing.
- `agents/builder.md` keeps builder as implementation owner.
- `skills/build/SKILL.md` limits scout usage and requires summary before edits.

Add smoke tests later if the runtime exposes scout invocations directly.

## Risks

Risk: Too many scouts increase cost and noise.

Mitigation: Limit to one to three scouts by default.

Risk: Scouts produce conflicting advice.

Mitigation: Builder must decide and own the final implementation.

Risk: Scouts accidentally become hidden implementers.

Mitigation: Scout contract forbids edits; builder remains the only code owner.

Risk: Orchestrator state becomes harder to audit.

Mitigation: Scouts are not FSM stages. They are builder-internal research unless
future versions add explicit event logging.

## Recommendation

Implement scout delegation, but keep it read-only in the first version.

This gives builder parallel context gathering without turning implementation
ownership into chaos. It should improve quality on medium and complex changes
while preserving the framework's strongest property: clear ownership boundaries.
