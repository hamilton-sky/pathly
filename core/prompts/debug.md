# debug - Bug Workflow

Investigate a known symptom, reproduce it, find the root cause, fix it, and
verify the before/after behavior.

## Outputs

Debug work lives under:

```text
debugs/<symptom>/
  SYMPTOM.md
  REPRO.md
  ROOT_CAUSE.md
  FIX.md
  feedback/
```

## Flow

1. Capture the symptom.
2. Reproduce or explain why it cannot be reproduced.
3. Identify the root cause.
4. Implement the fix.
5. Verify the fix.
6. Record what changed.
