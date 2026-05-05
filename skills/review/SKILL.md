---
name: review
description: Review code changes against project architectural rules and conventions. Reads ARCHITECTURE_PROPOSAL.md and .claude/rules/ to check for violations. Works with any project.
argument-hint: "[file-path | 'staged' | 'last']"
---

## Pathly Command Surface

Use `/pathly <command>` as the canonical cross-framework command form. `/path <command>` is the short alias. Legacy direct skill commands may remain available in some hosts for backwards compatibility, but user-facing guidance should prefer `/pathly` or `/path`.

Review code at $ARGUMENTS against this project's architectural standards.

- `staged` or empty → review `git diff --staged`
- `last` → review `git diff HEAD~1 HEAD`
- file path → review that specific file

## Step 1 — Get the diff

Run the appropriate git diff command based on `$ARGUMENTS`.

## Step 2 — Load project rules

Read (if present):
1. The `ARCHITECTURE_PROPOSAL.md` in the `plans/*/` folder that most closely matches the changed files — defines the intended architecture for in-progress work
2. All `.md` files in `.claude/rules/` — project-wide architectural contracts

If neither exists, review against general software engineering good practices and note the absence.

## Step 3 — Check for violations

For each changed file, check:

### Dependency direction
- Does the file import from a layer it should not depend on?
- Does the dependency direction match what `ARCHITECTURE_PROPOSAL.md` specifies?

### Layer responsibility
- Does the file contain logic that belongs in a different layer?
- Are concerns properly separated (e.g., data access vs. business logic vs. presentation)?

### Conventions
- Does the file follow naming and structural conventions shown in `.claude/rules/`?
- Are interfaces and contracts implemented correctly per the rules files?

### Scope
- Does the change touch files outside the scope described in the active conversation plan?
- Are there unexpected side effects on other modules?

## Report format

List each check as PASS / FAIL / N/A.

For failures use these prefixes:
```
[ARCH] <file>:<line> — <what the violation is> — <what it should be instead>
[IMPL] <file>:<line> — <what the violation is> — <fix required>
```

If all checks pass: `PASS — no violations found.`

If violations found: list each one. Do NOT auto-fix. Report only.
