# Scout Delegation — Implementation Plan

## Overview

Adds a read-only `scout` subagent that `builder` can spawn (up to three, in parallel) to gather
codebase context before implementing a change. Scout is builder-internal: invisible to the
orchestrator FSM, advisory-only, incapable of writing files. Three load-bearing rules are
documented in two places each: (1) max-3-scouts-per-conversation, (2) summarize-before-editing,
(3) scout is read-only. No Python changes; all changes are agent markdown files.

## Layer Architecture

```
builder (agents/builder.md)
     │  spawns via Agent tool: subagent_type="scout", model=haiku
     ▼
scout (agents/scout.md)  ←── read-only, no writes, no feedback files
     │  returns Structured Findings
     ▼
builder compresses findings → summary → begins edits
```

build skill (skills/build/SKILL.md) restates constraints for builder reading the skill.

## Phases

### Phase 1: Create agents/scout.md (15 min)
**Layer:** Agent definition
**Delivers stories:** S1.1
**Files:**
- `agents/scout.md` — NEW: read-only scout agent

**Details:**
- Frontmatter: `name: scout`, `role: analyst`, `model: haiku`
- Body must include:
  - Explicit no-edit language: "Do NOT write to any file. Do NOT edit or create any file. Do NOT create feedback files (IMPL_QUESTIONS.md, DESIGN_QUESTIONS.md, HUMAN_QUESTIONS.md). Do NOT spawn additional agents. Scout is read-only."
  - Structured Findings output format: `## Findings`, `## Recommendation` sections
  - Quick vs Scout decision table (identical to the one in STORM_SEED.md)
  - Rule: if scout surfaces ambiguity, flag it in findings; builder writes the feedback file
- Model: haiku (same as quick — lightweight, fast)

**Verify:**
```
grep -i "do not.*edit\|do not write\|read.only\|cannot.*write" agents/scout.md
```

---

### Phase 2: Update agents/builder.md (20 min)
**Layer:** Agent definition
**Delivers stories:** S1.2
**Files:**
- `agents/builder.md` — UPDATE: add scout delegation section

**Details:**
Add a new section "Scout delegation" after the existing "When blocked — inline quick vs feedback
file" section. The section must include:
1. The Quick vs Scout decision table:
   | Dimension | Quick | Scout |
   |---|---|---|
   | Typical tool calls | ≤ 2 | 5–15 |
   | Output shape | 1-line answer, a value, a path | Structured Findings + Recommendation |
   | Lifetime | Ephemeral inline answer | Findings collected before builder edits |
   | Example questions | "Does this file exist?" / "What is on line 42?" | "How do all modals work?" / "Where are API errors surfaced?" |
2. Max-3-scouts limit (doc-only): "Spawn at most 3 scouts per conversation."
3. Summarize-before-editing rule (prominent — mark it **load-bearing**):
   "After all scouts return, compress findings into a short summary before touching any file.
   Raw scout output must not persist into the edit phase — it bloats context and causes drift."
4. Builder remains the single implementation owner: scouts are advisory only.
5. Invocation pattern: `Agent(subagent_type="scout", model="haiku", prompt="...")`
6. If a scout surfaces ambiguity → builder writes the appropriate feedback file (not the scout).

**Verify:**
```
grep -i "scout" agents/builder.md
grep -i "summarize\|summary.*before\|before.*edit" agents/builder.md
```

---

### Phase 3: Update skills/build/SKILL.md (15 min)
**Layer:** Skill definition
**Delivers stories:** S2.1
**Files:**
- `skills/build/SKILL.md` — UPDATE: add scout delegation section

**Details:**
Add a "Scout delegation" section near the top of the skill (after the mode selection or pre-flight
check section). The section must include:
- When to spawn a scout: when builder needs to read 3+ files across multiple directories before
  making implementation decisions.
- Max-3-scouts limit per conversation.
- Summarize-before-editing rule: compress all scout findings into a short summary before any file
  edits begin.
- Scout is read-only: cannot create feedback files, cannot spawn further agents.
- Quick vs Scout reminder: if the answer fits in ≤ 2 tool calls, use quick, not scout.

**Verify:**
```
grep -i "scout" skills/build/SKILL.md
grep -i "summarize\|summary.*before\|before.*edit\|max.*3\|three.*scout\|3.*scout" skills/build/SKILL.md
```

---

### Phase 4: Static assertions (5 min)
**Layer:** Verification
**Delivers stories:** S2.2
**Files:** none (read-only verification)

**Details:**
Run the four grep assertions from the storm seed to confirm all load-bearing rules are present:
1. `agents/scout.md` contains explicit no-edit language
2. `agents/builder.md` states builder is the sole implementation owner
3. `skills/build/SKILL.md` limits scouts to three per conversation
4. `skills/build/SKILL.md` requires summary before edits

**Verify:**
```
grep -i "do not.*edit\|do not write\|read.only" agents/scout.md && echo "PASS: scout no-edit language" || echo "FAIL"
grep -i "implementation owner\|sole.*owner\|advisory" agents/builder.md && echo "PASS: builder as owner" || echo "FAIL"
grep -i "max.*3\|3.*scout\|three.*scout" skills/build/SKILL.md && echo "PASS: max-3 cap" || echo "FAIL"
grep -i "summarize\|summary.*before\|before.*edit" skills/build/SKILL.md && echo "PASS: summarize rule" || echo "FAIL"
```

---

## Prerequisites
- `agents/quick.md` exists (scout is modelled after quick but with richer output format)
- `agents/builder.md` exists (will be updated, not replaced)
- `skills/build/SKILL.md` exists (will be updated, not replaced)

## Key Decisions
- Scout uses `model: haiku` — same lightweight model as quick; investigations are read-only and don't require reasoning depth
- Max-3 is doc-only in v1 — no runtime counter; norm established through documentation
- Orchestrator FSM is not modified — scouts are builder-internal only
- Scout cannot write feedback files — if ambiguity is found, builder writes the file based on scout findings
