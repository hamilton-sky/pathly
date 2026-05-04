# Scout Delegation — Conversation Guide

Split into 2 conversations. Each leaves the codebase in a consistent state.
After each conversation, **commit your changes** before starting the next.

---

## Conversation 1: Create scout agent + update builder (Phases 1–2)

**Stories delivered:** S1.1, S1.2

**Prompt to paste:**
```
Implement scout-delegation Conversation 1 (Phases 1–2) from plans/scout-delegation/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 1: Create agents/scout.md — a new read-only scout agent.
  - Frontmatter: name: scout, role: analyst, model: haiku
  - Body must contain ALL of the following:
    - Explicit no-edit language: "Do NOT write to any file. Do NOT edit or create any file.
      Do NOT create feedback files. Do NOT spawn additional agents. Scout is read-only."
    - Structured Findings output format with ## Findings and ## Recommendation sections
    - Quick vs Scout decision table (columns: Dimension, Quick, Scout; rows: Typical tool calls,
      Output shape, Lifetime, Example questions — see STORM_SEED.md or IMPLEMENTATION_PLAN.md)
    - Rule: if scout surfaces ambiguity, flag it in findings; builder (not scout) writes the
      feedback file
  - Model haiku (lightweight, fast, same as quick)

- Phase 2: Update agents/builder.md — add a "Scout delegation" section after the existing
  "When blocked — inline quick vs feedback file" section.
  The section must include:
  1. Quick vs Scout decision table (same table as in scout.md)
  2. Max-3-scouts-per-conversation cap (doc-only)
  3. Summarize-before-editing rule — mark it **load-bearing**:
     "After all scouts return, compress findings into a short summary before touching any file."
  4. Builder remains the single implementation owner; scout output is advisory only
  5. Invocation pattern: Agent(subagent_type="scout", model="haiku", prompt="...")
  6. If scout surfaces ambiguity → builder writes the appropriate feedback file

Do NOT touch skills/build/SKILL.md, agents/README.md, or any other file.

Verify:
  grep -i "do not.*edit\|do not write\|read.only" agents/scout.md
  grep -i "scout" agents/builder.md
  grep -i "summarize\|summary.*before\|before.*edit" agents/builder.md

After done, update plans/scout-delegation/PROGRESS.md phases 1–2 to DONE and Conv 1 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** `agents/scout.md` exists with no-edit language and decision table; `agents/builder.md` has a new Scout delegation section with the summarize-before-editing rule.

**Files touched:** `agents/scout.md` (new), `agents/builder.md` (updated), `plans/scout-delegation/PROGRESS.md` (updated)

---

## Conversation 2: Update build skill + static assertions (Phases 3–4)

**Stories delivered:** S2.1, S2.2

**Prompt to paste:**
```
Conversation 1 is DONE (agents/scout.md created, agents/builder.md updated with scout delegation section).

Implement scout-delegation Conversation 2 (Phases 3–4) from plans/scout-delegation/IMPLEMENTATION_PLAN.md.

Scope:
- Phase 3: Update skills/build/SKILL.md — add a "Scout delegation" section.
  Place it after the pre-flight check section (Step 1). The section must include:
  - When to spawn a scout: when builder needs to read 3+ files across multiple directories
    before making implementation decisions
  - Max-3-scouts-per-conversation limit
  - Summarize-before-editing rule: compress all scout findings into a short summary before
    any file edits begin
  - Scout is read-only: cannot create feedback files, cannot spawn further agents
  - Quick vs Scout reminder: if the answer fits in ≤ 2 tool calls, use quick, not scout

- Phase 4: Run these static grep assertions (all four must pass):
  grep -i "do not.*edit\|do not write\|read.only" agents/scout.md && echo "PASS: scout no-edit" || echo "FAIL"
  grep -i "implementation owner\|sole.*owner\|advisory" agents/builder.md && echo "PASS: builder as owner" || echo "FAIL"
  grep -i "max.*3\|3.*scout\|three.*scout" skills/build/SKILL.md && echo "PASS: max-3 cap" || echo "FAIL"
  grep -i "summarize\|summary.*before\|before.*edit" skills/build/SKILL.md && echo "PASS: summarize rule" || echo "FAIL"

Also run existing tests to confirm no regressions:
  pytest tests/ -q

Do NOT touch agents/scout.md or agents/builder.md in this conversation.

After all four assertions print PASS and pytest passes, update plans/scout-delegation/PROGRESS.md
phases 3–4 to DONE, Conv 2 to DONE, and overall Status to COMPLETE.

If any assertion prints FAIL, fix the relevant file and re-run before marking DONE.
If verification fails and the fix requires out-of-scope changes, stop and report.
```

**Expected output:** `skills/build/SKILL.md` has a scout delegation section; all four grep assertions print PASS; `pytest tests/ -q` passes.

**Files touched:** `skills/build/SKILL.md` (updated), `plans/scout-delegation/PROGRESS.md` (updated)
