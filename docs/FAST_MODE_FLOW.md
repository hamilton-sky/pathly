# Fast Mode Flow

Fast mode skips human pause points where the workflow can safely continue. It
does not bypass feedback files, retry limits, missing prerequisites, or strict
approval requirements.

## Current Entry Points

Claude Code:

```text
/pathly flow <feature> fast
/pathly flow <feature> build fast
```

CLI:

```text
pathly flow <feature> --fast
pathly run <feature> --entry build --fast
```

Codex:

```text
Use Pathly flow for <feature> fast
```

## Behavior

```text
request
  |
  v
startup checks
  |-- missing prerequisite -> stop
  |-- open feedback file -> stop or route to owner
  `-- clean -> continue
  |
  v
discovery / planning
  |
  v
rigor escalator
  |-- no signals -> keep lite plan
  `-- signals -> add recommended files automatically in fast mode
  |
  v
build / review loop
  |-- REVIEW_FAILURES.md -> builder fixes
  |-- ARCH_FEEDBACK.md -> architect resolves
  |-- HUMAN_QUESTIONS.md -> stop
  `-- pass -> next conversation
  |
  v
test loop
  |-- TEST_FAILURES.md -> builder fixes
  `-- pass -> retro / done
```

## Hard Stops

Fast mode still stops for:

- `HUMAN_QUESTIONS.md`
- unresolved feedback files
- retry limit exceeded
- zero-diff stalls
- missing required plan files
- unavailable runner tooling
- `strict` workflows that require explicit human approval

## Rigor Interaction

Rigor controls process depth. Fast controls pauses.

| Rigor | Fast behavior |
|---|---|
| `nano` | Minimal path; fast may continue after checks. |
| `lite` | Default planning depth; escalator additions can be applied automatically. |
| `standard` | Full plan file set and normal gates, with pauses skipped where allowed. |
| `strict` | Must reject or ignore fast automation unless a future project explicitly opts in. |

The current Python CLI exposes fast as `--fast` on `pathly flow`, `pathly run`,
and `pathly team-flow`.
