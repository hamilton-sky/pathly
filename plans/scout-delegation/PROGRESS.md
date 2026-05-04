# Scout Delegation — Progress

## Status: NOT STARTED

## Story Status

| Story | Title | Delivered by | Status |
|-------|-------|--------------|--------|
| S1.1 | Scout agent file exists as a named, read-only agent | Conv 1 | TODO |
| S1.2 | Builder knows when to use scout vs quick | Conv 1 | TODO |
| S2.1 | Build skill documents scout constraints | Conv 2 | TODO |
| S2.2 | Static assertions verify all three files | Conv 2 | TODO |

## Conversation Breakdown

| Conv | Phases | Stories | Status | Verify |
|------|--------|---------|--------|--------|
| 1 | 1–2 | S1.1, S1.2 | TODO | `grep -i "do not.*edit\|read.only" agents/scout.md && grep -i "scout" agents/builder.md` |
| 2 | 3–4 | S2.1, S2.2 | TODO | `grep -i "scout" skills/build/SKILL.md && grep -i "summarize\|summary.*before" skills/build/SKILL.md` |

See **CONVERSATION_PROMPTS.md** for exact prompts to paste in each conversation.

## Phase Detail

| # | Phase | Layer | Description | Conv | Status | Key Files |
|---|-------|-------|-------------|------|--------|-----------|
| 1 | Create scout.md | Agent definition | New read-only scout agent file | 1 | TODO | `agents/scout.md` |
| 2 | Update builder.md | Agent definition | Add scout delegation section | 1 | TODO | `agents/builder.md` |
| 3 | Update build SKILL.md | Skill definition | Add scout constraints section | 2 | TODO | `skills/build/SKILL.md` |
| 4 | Static assertions | Verification | Grep all three files for load-bearing rules | 2 | TODO | — |

## Prerequisites
- `agents/quick.md` exists (scout mirrors its structure)
- `agents/builder.md` exists
- `skills/build/SKILL.md` exists

## Blocked By
- Nothing
