# Scout Delegation — Conversation Guide

Split into 2 conversations. Each leaves the codebase in a consistent state.
After each conversation, **commit your changes** before starting the next.

---

## Conversation 1: Create scout agent + update builder (Phases 1–2) ✅ DONE

**Stories delivered:** S1.1, S1.2
**Status:** Complete — `agents/scout.md` and `agents/builder.md` updated.

---

## Conversation 2: Update build skill + static assertions (Phases 3–4)

**Stories delivered:** S2.1, S2.2

**Prompt to paste:**
```
Conversations 1 is DONE (agents/scout.md created, agents/builder.md updated).
Phases 5–9 are also DONE out-of-band (agents/web-researcher.md created; agents/architect.md,
agents/planner.md, agents/reviewer.md, agents/tester.md all updated with sub-agent sections).

Implement scout-delegation Conversation 2 (Phases 3–4) from plans/scout-delegation/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 3: Update skills/build/SKILL.md — add a "Scout delegation" section.
  Place it after the pre-flight check section (Step 1). The section must include:
  - When to spawn a scout: when builder needs to read 3+ files across directories before deciding
  - Max-4 sub-agents limit per conversation (not max-3 — the ladder has grown to include
    web-researcher; the cap is 4 shared across all sub-agent types)
  - Summarize-before-editing rule: compress all sub-agent findings into a short summary before
    any file edits begin
  - Scout is read-only: cannot create feedback files, cannot spawn further agents
  - Quick vs Scout reminder: if the answer fits in ≤ 2 tool calls, use quick, not scout

- Phase 4: Run these static grep assertions — all must print PASS:
  grep -i "do not.*edit\|do not write\|read.only" agents/scout.md && echo "PASS: scout no-edit" || echo "FAIL"
  grep -i "implementation owner\|sole.*owner\|advisory" agents/builder.md && echo "PASS: builder as owner" || echo "FAIL"
  grep -i "max.*4\|4.*sub\|four.*sub" agents/builder.md && echo "PASS: builder max-4 cap" || echo "FAIL"
  grep -i "max.*4\|4.*sub\|four.*sub" skills/build/SKILL.md && echo "PASS: skill max-4 cap" || echo "FAIL"
  grep -i "summarize\|summary.*before\|before.*edit" skills/build/SKILL.md && echo "PASS: skill summarize rule" || echo "FAIL"
  grep -i "do not.*edit\|do not write\|read.only" agents/web-researcher.md && echo "PASS: web-researcher no-edit" || echo "FAIL"

Do NOT touch agents/scout.md, agents/builder.md, agents/web-researcher.md,
agents/architect.md, agents/planner.md, agents/reviewer.md, or agents/tester.md.

After all six assertions print PASS, update plans/scout-delegation/PROGRESS.md:
- Phases 3–4 → DONE
- Conv 2 → DONE
- Overall Status → COMPLETE

If any assertion prints FAIL, fix the relevant file and re-run before marking DONE.
```

**Expected output:** `skills/build/SKILL.md` has a scout delegation section with max-4 cap;
all six grep assertions print PASS.

**Files touched:** `skills/build/SKILL.md` (updated), `plans/scout-delegation/PROGRESS.md` (updated)
