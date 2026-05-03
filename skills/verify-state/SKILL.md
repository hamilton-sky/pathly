---
name: verify-state
description: Consistency check — detects stale feedback files, PROGRESS.md drift from git, and plan files pointing to deleted code. Run before resuming a feature pipeline or when something feels off.
argument-hint: "[feature-name]"
---

Run a consistency check on the feature plan pipeline. If `$ARGUMENTS` is given, check that feature only. If blank, check all features in `plans/`.

---

## Step 1 — Find features to check

If `$ARGUMENTS` is given:
- Check `plans/$ARGUMENTS/` exists. If not: stop → `plans/$ARGUMENTS/ not found.`
- Set `FEATURES = [$ARGUMENTS]`

If no argument:
- List all subdirectories of `plans/` that contain `PROGRESS.md`
- Set `FEATURES = that list`

---

## Step 2 — For each feature, run 3 checks

### Check A — Stale feedback files

```bash
ls plans/$FEATURE/feedback/ 2>/dev/null
```

For each `.md` file found in `plans/$FEATURE/feedback/`:
- It represents an **open, unresolved issue**
- Check git log for commits made *after* this file's modification time:
  ```bash
  git log --oneline --since="$(git log -1 --format='%ci' -- plans/$FEATURE/feedback/<file>)" -- . 2>/dev/null | head -5
  ```
- **Flag if:** the feedback file exists AND no commits have been made after it was last modified
- Report as: `[STALE FEEDBACK] plans/$FEATURE/feedback/<file> — open since <date>, no commits since`

---

### Check B — PROGRESS.md DONE items with no matching file coverage

Read `plans/$FEATURE/PROGRESS.md` and `plans/$FEATURE/IMPLEMENTATION_PLAN.md`.

For each conversation marked DONE in `PROGRESS.md`:
- Extract the files that conversation was expected to touch from `IMPLEMENTATION_PLAN.md` (look for file paths listed under that conversation's phase/section)
- Get the full set of files changed on this branch vs. the base branch:
  ```bash
  git diff $(git merge-base HEAD main)...HEAD --name-only -- . ":(exclude)plans/" 2>/dev/null
  ```
- **Flag if:** a conversation is marked DONE but **none** of its expected files appear in the branch diff

If `IMPLEMENTATION_PLAN.md` does not list expected files per conversation, fall back to:
- Count DONE conversations vs. count files changed on branch outside `plans/`
- Flag if DONE count > 0 and changed file count is 0 (nothing was ever committed)

Report as: `[PROGRESS DRIFT] $FEATURE — conversation 'N' marked DONE but none of its expected files appear in branch diff`

---

### Check C — Plan files pointing to deleted code

Read `plans/$FEATURE/ARCHITECTURE_PROPOSAL.md` and `plans/$FEATURE/IMPLEMENTATION_PLAN.md`.

Extract all file paths mentioned (patterns: `poms/`, `stepper/`, `.py`, `.ts`, `.js`):
```bash
grep -oE "(poms|stepper|exam|src)/[a-zA-Z0-9_./-]+" plans/$FEATURE/ARCHITECTURE_PROPOSAL.md plans/$FEATURE/IMPLEMENTATION_PLAN.md 2>/dev/null | sort -u
```

For each path found:
- Check if the file exists: does it exist in the working tree?
- **Flag if:** a path is mentioned in the plan but the file does not exist

Report as: `[DEAD REFERENCE] plans/$FEATURE — '<path>' mentioned in plan but not found on disk`

---

## Step 3 — Report

Print a structured summary:
```text
╔══════════════════════════════════════════╗
  verify-state — $FEATURE (or: all features)
╚══════════════════════════════════════════╝

✓  No issues        ← if everything clean
⚠  N issue(s) found ← if problems detected

[STALE FEEDBACK]    plans/.../feedback/REVIEW_FAILURES.md — open since 2026-04-28, no commits since
[PROGRESS DRIFT]    hotel-search — 3 conversations DONE but only 1 implementation commit found
[DEAD REFERENCE]    nl-workflow-compiler — 'stepper/engine/planner/nl_compiler.py' mentioned but not found
```

If all clear: `All checks passed. Pipeline state looks consistent.`

If issues found: list each one. Do NOT auto-fix. Report only.

---

## Rules

- **Read-only:** Never edit files, never delete feedback files.
- **Objective:** Do not make assumptions about correctness — report what the data shows.
- **Robustness:** If a check cannot run (git not available, file unreadable), report that check as SKIPPED, not PASS.
- **Context:** Dead references in `CONVERSATION_PROMPTS.md` are common and expected (future work) — only flag `ARCHITECTURE_PROPOSAL.md` and `IMPLEMENTATION_PLAN.md`.
```
