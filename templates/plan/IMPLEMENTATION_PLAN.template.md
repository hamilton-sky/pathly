# [Feature Name] — Implementation Plan

## Overview
[What this feature adds — which site, which actions, which workflow, 2-3 sentences]

## Layer Architecture
[Show how the feature spans POM / Glue / Flow layers]

```
Flow (JSON)  →  Glue (stepper/sites/…)  →  POM (poms/…)
   ↓                    ↓                        ↓
[workflow]         [action classes]         [locators + interactions]
```

## Phases

### Phase 1: [Phase Title] (estimated effort)
**Layer:** POM / Glue / Flow / Engine
**Delivers stories:** S1.1, S1.2
**Files:**
- `poms/<site>/pages/<file>.py` — [what changes]
- `stepper/sites/<site>/pages/<file>.py` — NEW: [what it does]

**Details:**
[Specific implementation instructions — cfg list keys, method signatures, action names]

**Verify:** `pytest exam/` or `python stepper/main.py --workflow stepper/sites/<site>/workflows/<file>.json --show`

### Phase 2: [Phase Title] (estimated effort)
...

## Prerequisites
- [What must be true before starting]

## Key Decisions
- [Architecture decision 1 and rationale — e.g., which resolver keys to use]
- [Architecture decision 2 and rationale]
