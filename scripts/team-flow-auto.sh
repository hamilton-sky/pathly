#!/bin/bash
# team-flow-auto.sh — Run the full team-flow pipeline in fresh claude sessions
#
# Each stage spawns a new `claude -p` process so context never accumulates
# across conversations. Plan files + feedback files are the shared state.
#
# Usage:
#   bash scripts/team-flow-auto.sh <feature>
#   bash scripts/team-flow-auto.sh <feature> --entry build
#   bash scripts/team-flow-auto.sh <feature> --entry test
#
# Prerequisites:
#   - Claude Code CLI installed and authenticated (claude command available)
#   - Working directory is repo root (claude-agents-framework/)
#   - Git working directory is clean before each build conversation

set -euo pipefail

FEATURE="${1:?Usage: bash scripts/team-flow-auto.sh <feature-name> [--entry build|test]}"
ENTRY_STAGE="discovery"
MAX_FEEDBACK_CYCLES=2

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --entry) ENTRY_STAGE="${2:?--entry requires build or test}"; shift ;;
    build|test) ENTRY_STAGE="$1" ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
  shift
done

PLAN_DIR="plans/$FEATURE"
PROGRESS_FILE="$PLAN_DIR/PROGRESS.md"
FEEDBACK_DIR="$PLAN_DIR/feedback"

mkdir -p logs
LOG_FILE="logs/team-flow-${FEATURE}-$(date +%Y%m%d_%H%M%S).log"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }
banner() {
  echo -e "\n${BLUE}══════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
  echo -e "${BLUE}  $*${NC}" | tee -a "$LOG_FILE"
  echo -e "${BLUE}══════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
}

# Run a claude CLI session. Returns exit code; output goes to log + stdout.
run_claude() {
  local prompt="$1"
  local exit_code=0
  log "${CYAN}>>> $prompt${NC}"
  echo "" | tee -a "$LOG_FILE"
  claude -p "$prompt" \
    --allowedTools "Edit,Write,Read,Glob,Grep,Bash,Skill,TodoWrite,WebSearch,WebFetch,Agent" \
    2>&1 | tee -a "$LOG_FILE" || exit_code=$?
  echo "" | tee -a "$LOG_FILE"
  return $exit_code
}

check_complete()        { grep -qi "Status: COMPLETE" "$PROGRESS_FILE" 2>/dev/null; }
feedback_exists()       { [[ -f "$FEEDBACK_DIR/$1" ]]; }
git_is_clean()          { [[ -z "$(git status --porcelain)" ]]; }
count_remaining()       {
  sed -n '/## Conversation Breakdown/,/^## /p' "$PROGRESS_FILE" 2>/dev/null \
    | grep -c "| TODO |" 2>/dev/null || echo "0"
}

# ── Pre-flight ────────────────────────────────────────────────────────────────
if ! command -v claude &>/dev/null; then
  echo -e "${RED}Error: 'claude' CLI not found. Install Claude Code first.${NC}"
  exit 1
fi

banner "team-flow-auto: $FEATURE  (entry: $ENTRY_STAGE)"
log "Log: $LOG_FILE"

# ── STAGE 1 — Storm ──────────────────────────────────────────────────────────
if [[ "$ENTRY_STAGE" == "discovery" ]]; then
  banner "STAGE 1 — Storm (architect / opus)"
  run_claude "/storm $FEATURE" || {
    log "${RED}Storm failed. Stopping.${NC}"; exit 1
  }
else
  log "[SKIPPED] Stage 1 (storm)"
fi

# ── STAGE 2 — Plan ───────────────────────────────────────────────────────────
if [[ "$ENTRY_STAGE" == "discovery" ]]; then
  banner "STAGE 2 — Plan (planner / sonnet)"
  run_claude "/plan $FEATURE" || {
    log "${RED}Plan failed. Stopping.${NC}"; exit 1
  }
else
  log "[SKIPPED] Stage 2 (plan)"
fi

# Verify plan exists before build loop
if [[ ! -f "$PROGRESS_FILE" ]]; then
  log "${RED}Error: $PROGRESS_FILE not found. Run without --entry first.${NC}"
  exit 1
fi

# ── STAGE 3 — Implement + Review Loop ────────────────────────────────────────
if [[ "$ENTRY_STAGE" != "test" ]]; then
  banner "STAGE 3 — Implement + Review Loop"
  CONV=0

  while ! check_complete; do
    REMAINING=$(count_remaining)
    [[ "$REMAINING" -eq 0 ]] && break

    CONV=$((CONV + 1))
    FEEDBACK_CYCLES=0
    log "${YELLOW}── Conversation $CONV  ($REMAINING remaining) ──${NC}"

    # Each conversation must start from a clean git state
    if ! git_is_clean; then
      log "${RED}Working directory not clean before conv $CONV. Commit or stash first.${NC}"
      git status --short | tee -a "$LOG_FILE"
      exit 1
    fi

    # 3a — Build
    run_claude "/build $FEATURE auto" || {
      log "${RED}Build conv $CONV failed. Stopping.${NC}"; exit 1
    }

    # 3b — Review (direct prompt — /review skill is playwright-specific)
    run_claude "You are an adversarial reviewer for the $FEATURE feature.

Run: git diff HEAD -- . ':(exclude)plans/'
Review the changes from the last commit against:
  - plans/$FEATURE/ARCHITECTURE_PROPOSAL.md (architectural contracts)
  - plans/$FEATURE/IMPLEMENTATION_PLAN.md (implementation scope)
  - Any rules in .claude/rules/ if that directory exists

If you find architectural violations (wrong layer, wrong dependency direction, broken contracts):
  Write plans/$FEATURE/feedback/ARCH_FEEDBACK.md using this format:
    [ARCH] <file>:<line> — <what the violation is> — <what it should be instead>

If you find implementation violations (scope creep, wrong patterns, missing requirements):
  Write plans/$FEATURE/feedback/REVIEW_FAILURES.md using this format:
    [IMPL] <file>:<line> — <what the violation is> — <fix required>

If no violations: report PASS and do NOT write any feedback files." || {
      log "${YELLOW}Reviewer exited non-zero — checking feedback files...${NC}"
    }

    # 3c — Feedback resolution loop
    while feedback_exists "ARCH_FEEDBACK.md" || feedback_exists "REVIEW_FAILURES.md"; do
      FEEDBACK_CYCLES=$((FEEDBACK_CYCLES + 1))
      if [[ $FEEDBACK_CYCLES -gt $MAX_FEEDBACK_CYCLES ]]; then
        log "${RED}Feedback loop exceeded $MAX_FEEDBACK_CYCLES cycles for conv $CONV.${NC}"
        log "${RED}Manual intervention required. Check $FEEDBACK_DIR/.${NC}"
        exit 1
      fi
      log "${YELLOW}  Feedback cycle $FEEDBACK_CYCLES of $MAX_FEEDBACK_CYCLES${NC}"

      if feedback_exists "ARCH_FEEDBACK.md"; then
        log "${YELLOW}  ARCH_FEEDBACK.md found — spawning architect...${NC}"
        run_claude "Read plans/$FEATURE/feedback/ARCH_FEEDBACK.md.
Redesign the affected architecture to resolve each [ARCH] item.
Update plans/$FEATURE/ARCHITECTURE_PROPOSAL.md with the revised design.
If conversation scopes need updating, also update plans/$FEATURE/IMPLEMENTATION_PLAN.md.
Delete plans/$FEATURE/feedback/ARCH_FEEDBACK.md when all items are resolved.
Report what changed." || { log "${RED}Architect resolve failed.${NC}"; exit 1; }

        # Rebuild after arch change
        run_claude "/build $FEATURE auto" || {
          log "${RED}Re-build after arch fix failed.${NC}"; exit 1
        }
      fi

      if feedback_exists "REVIEW_FAILURES.md"; then
        log "${YELLOW}  REVIEW_FAILURES.md found — spawning builder to fix...${NC}"
        DIFF_BEFORE=$(git diff HEAD -- . ":(exclude)plans/" 2>/dev/null || true)

        run_claude "Read plans/$FEATURE/feedback/REVIEW_FAILURES.md.
Fix each [IMPL] violation exactly as described.
Do not change anything outside the listed violations.
Delete plans/$FEATURE/feedback/REVIEW_FAILURES.md when all items are fixed." || {
          log "${RED}Builder fix failed.${NC}"; exit 1
        }

        # Zero-diff check — if builder made no code changes it's a stall
        DIFF_AFTER=$(git diff HEAD -- . ":(exclude)plans/" 2>/dev/null || true)
        if [[ "$DIFF_BEFORE" == "$DIFF_AFTER" ]]; then
          log "${RED}Zero-diff stall: builder made no changes after fix attempt.${NC}"
          mkdir -p "$FEEDBACK_DIR"
          {
            echo "[STALL] Conversation $CONV — zero-diff loop."
            echo "Builder claimed to fix REVIEW_FAILURES.md but no implementation code changed."
            echo "Human decision required: accept as-is, override the rule, or rewrite conv $CONV scope."
          } > "$FEEDBACK_DIR/HUMAN_QUESTIONS.md"
          log "${RED}Written: $FEEDBACK_DIR/HUMAN_QUESTIONS.md — manual intervention required.${NC}"
          exit 1
        fi

        # Re-review after fix
        run_claude "Re-review the latest implementation changes for the $FEATURE feature.
Run: git diff HEAD -- . ':(exclude)plans/'
Check for any remaining violations from plans/$FEATURE/feedback/ (if any files still exist).
If violations remain, rewrite the appropriate feedback file.
If all clear: report PASS and ensure no feedback files exist in $FEEDBACK_DIR." || {
          log "${YELLOW}  Re-review exited non-zero — rechecking feedback files...${NC}"
        }
      fi
    done

    log "${GREEN}  Conv $CONV — PASS${NC}"
  done

  log "${GREEN}All conversations complete.${NC}"
fi

# ── STAGE 4 — Test + Fix Loop ─────────────────────────────────────────────────
banner "STAGE 4 — Test + Fix Loop (tester / sonnet)"
TEST_RETRIES=0

while true; do
  run_claude "You are a tester verifying the $FEATURE feature.

Read plans/$FEATURE/USER_STORIES.md.
For each acceptance criterion, determine: PASS / FAIL / NOT COVERED.
  - Run the actual verify command from CONVERSATION_PROMPTS.md if available.
  - Read the implementation code to confirm the criterion is met.

Print a results table:
  | Criterion | Status | Notes |

If any criterion is FAIL or NOT COVERED:
  Write plans/$FEATURE/feedback/TEST_FAILURES.md using this format:
    [TEST-FAIL] <criterion summary> — <what is wrong> — <what needs to change>

If all PASS: report PASS and do NOT write TEST_FAILURES.md." || {
    log "${YELLOW}Tester exited non-zero — checking TEST_FAILURES.md...${NC}"
  }

  if ! feedback_exists "TEST_FAILURES.md"; then
    log "${GREEN}All acceptance criteria PASS.${NC}"
    break
  fi

  TEST_RETRIES=$((TEST_RETRIES + 1))
  if [[ $TEST_RETRIES -gt $MAX_FEEDBACK_CYCLES ]]; then
    log "${RED}Test failures unresolved after $MAX_FEEDBACK_CYCLES fix cycles.${NC}"
    log "${RED}Manual intervention required. Check $FEEDBACK_DIR/TEST_FAILURES.md.${NC}"
    exit 1
  fi

  log "${YELLOW}  TEST_FAILURES.md found (attempt $TEST_RETRIES) — spawning builder...${NC}"
  run_claude "Read plans/$FEATURE/feedback/TEST_FAILURES.md.
Fix each [TEST-FAIL] item so the acceptance criterion is satisfied.
Do not change anything beyond what is needed to pass the listed criteria.
Delete plans/$FEATURE/feedback/TEST_FAILURES.md when all items are resolved." || {
    log "${RED}Test fix failed.${NC}"; exit 1
  }
done

# ── STAGE 5 — Retro ──────────────────────────────────────────────────────────
banner "STAGE 5 — Retro (quick / haiku)"
run_claude "/retro $FEATURE" || {
  log "${YELLOW}Retro completed with warnings.${NC}"
}

banner "DONE — $FEATURE"
log "${GREEN}Full log: $LOG_FILE${NC}"
