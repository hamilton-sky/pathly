# Scout Delegation — Implementation Plan

## Overview

Defines a **4-level information gathering ladder** and applies it across all five agent roles.
No Python changes — all changes are agent markdown files and one skill file.

**Global rules (enforced in every agent's sub-agent section):**
1. Max 4 sub-agents total per session/conversation (shared pool)
2. Sub-agents are terminal — cannot spawn further agents
3. Compress all findings into a short summary before acting — raw output must not persist

## Ladder

| Level | Agent | Tool budget | Permitted by |
|-------|-------|-------------|--------------|
| 0 — Pre-flight | All | Glob/Grep inline | (no sub-agent) |
| 1 — Quick | All | ≤ 2 | all agents |
| 2 — Scout | local codebase | 5–15 | builder, architect, reviewer, tester |
| 3 — Web | external web | 5–10 | architect, planner |

## Layer Architecture

```
architect / planner
  ├── quick  (Level 1)
  ├── scout  (Level 2, architect only)
  └── web-researcher  (Level 3)

builder / reviewer / tester
  ├── quick  (Level 1)
  └── scout  (Level 2)

builder
  └── scout only — web-researcher explicitly excluded
      conflict rule: factual → third scout; architectural → DESIGN_QUESTIONS.md [ARCH]
```

## Phases

### Phase 1: Create agents/scout.md ✅ DONE
**Layer:** Agent definition | **Stories:** S1.1
**Files:** `agents/scout.md` — NEW

- Frontmatter: `name: scout`, `role: analyst`, `model: haiku`
- Explicit no-edit language, structured output (`## Findings`, `## Recommendation`, `## Ambiguities`)
- Quick vs Scout decision table

---

### Phase 2: Update agents/builder.md ✅ DONE
**Layer:** Agent definition | **Stories:** S1.2
**Files:** `agents/builder.md` — UPDATED

- Added "Information gathering — sub-agents" section
- Max-4 cap, summarize-before-editing (load-bearing), conflict resolution rule
- Web-researcher explicitly excluded

---

### Phase 3: Update skills/build/SKILL.md
**Layer:** Skill definition | **Stories:** S2.1
**Files:** `skills/build/SKILL.md` — UPDATE

Add a "Scout delegation" section after the pre-flight check. Must include:
- When to spawn a scout: 3+ file reads across directories before implementing
- Max-4 sub-agents limit (not max-3)
- Summarize-before-editing rule
- Scout is read-only; cannot create feedback files or spawn agents
- Quick vs Scout reminder: ≤ 2 tool calls → use quick

**Verify:**
```
grep -i "scout" skills/build/SKILL.md
grep -i "max.*4\|4.*sub\|four.*sub" skills/build/SKILL.md
grep -i "summarize\|summary.*before\|before.*edit" skills/build/SKILL.md
```

---

### Phase 4: Static assertions
**Layer:** Verification | **Stories:** S2.2
**Files:** none (read-only)

Run all assertions — all must print PASS:
```
grep -i "do not.*edit\|do not write\|read.only" agents/scout.md && echo "PASS: scout no-edit" || echo "FAIL"
grep -i "implementation owner\|sole.*owner\|advisory" agents/builder.md && echo "PASS: builder as owner" || echo "FAIL"
grep -i "max.*4\|4.*sub\|four.*sub" agents/builder.md && echo "PASS: builder max-4 cap" || echo "FAIL"
grep -i "max.*4\|4.*sub\|four.*sub" skills/build/SKILL.md && echo "PASS: skill max-4 cap" || echo "FAIL"
grep -i "summarize\|summary.*before\|before.*edit" skills/build/SKILL.md && echo "PASS: skill summarize rule" || echo "FAIL"
grep -i "do not.*edit\|do not write\|read.only" agents/web-researcher.md && echo "PASS: web-researcher no-edit" || echo "FAIL"
```

---

### Phase 5: Create agents/web-researcher.md ✅ DONE
**Layer:** Agent definition | **Stories:** S3.1
**Files:** `agents/web-researcher.md` — NEW

- Frontmatter: `name: web-researcher`, `role: analyst`, `model: haiku`
- Budget: 5–10 WebSearch/WebFetch calls
- Prompt injection guard
- Output: `## Findings`, `## Recommendation`, `## Sources`, `## Confidence`
- Explicit no-edit, no-spawn constraints

---

### Phase 6: Update agents/architect.md ✅ DONE
**Layer:** Agent definition | **Stories:** S3.2
**Files:** `agents/architect.md` — UPDATED

- Added "Information gathering — sub-agents" section
- Levels 1, 2, 3 all permitted (quick, scout, web-researcher)
- Max-4 cap, sub-agents are terminal

---

### Phase 7: Update agents/planner.md ✅ DONE
**Layer:** Agent definition | **Stories:** S3.3
**Files:** `agents/planner.md` — UPDATED

- Added "Information gathering — sub-agents" section
- Levels 1 and 3 permitted (quick, web-researcher); scout NOT permitted
- Max-4 cap

---

### Phase 8: Update agents/reviewer.md ✅ DONE
**Layer:** Agent definition | **Stories:** S3.4
**Files:** `agents/reviewer.md` — UPDATED

- Added "Information gathering — sub-agents" section
- Levels 1 and 2 permitted (quick, scout); web-researcher NOT permitted
- Max-4 cap

---

### Phase 9: Update agents/tester.md ✅ DONE
**Layer:** Agent definition | **Stories:** S3.5
**Files:** `agents/tester.md` — UPDATED

- Added "Information gathering — sub-agents" section
- Levels 1 and 2 permitted (quick, scout); web-researcher NOT permitted
- Max-4 cap

---

## Remaining Work

Only Phases 3 and 4 remain. Delivered by Conversation 2.

## Key Decisions
- Max cap is **4** (not 3) — covers the expanded multi-agent ladder
- Web-researcher is excluded from builder — builder stays local; only architect/planner need external knowledge
- Planner uses web-researcher but not scout — planner is requirements-focused, not implementation-focused
- Scout cannot write feedback files — builder writes them based on scout's `## Ambiguities`
- Orchestrator FSM is not modified — all sub-agents are internal to the calling agent
