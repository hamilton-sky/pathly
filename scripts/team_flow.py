#!/usr/bin/env python3
"""
team_flow.py — Python FSM driver for the claude-agents-framework pipeline.

Replaces team-flow-auto.sh. Uses orchestrator/ for deterministic state
tracking. Each agent runs in a fresh `claude -p` subprocess.

Usage:
  python scripts/team_flow.py <feature>
  python scripts/team_flow.py <feature> --entry build
  python scripts/team_flow.py <feature> --entry test
  python scripts/team_flow.py <feature> --fast
  python scripts/team_flow.py <feature> --recover
"""

import sys
import os
import subprocess
import json
import argparse
from pathlib import Path
from datetime import datetime

# Import orchestrator from repo root regardless of where this script is called from
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator.state import State
from orchestrator.events import (
    CommandEvent, AgentDoneEvent, FileCreatedEvent, FileDeletedEvent,
    HumanResponseEvent, NoDiffDetectedEvent, ImplementCompleteEvent,
    StateTransitionEvent, SystemEvent,
)
from orchestrator.reducer import reduce
from orchestrator.eventlog import EventLog
from orchestrator.constants import FSMState, Agent, FeedbackFile, Mode, Events

ALLOWED_TOOLS = "Edit,Write,Read,Glob,Grep,Bash,Skill,TodoWrite,WebSearch,WebFetch,Agent"
MAX_RETRIES = 2

# Feedback files in priority order (highest first)
FEEDBACK_PRIORITY = [
    FeedbackFile.HUMAN_QUESTIONS,
    FeedbackFile.ARCH_FEEDBACK,
    FeedbackFile.DESIGN_QUESTIONS,
    FeedbackFile.IMPL_QUESTIONS,
    FeedbackFile.REVIEW_FAILURES,
    FeedbackFile.TEST_FAILURES,
]


class Driver:
    def __init__(self, feature: str, mode: str, entry: str):
        self.feature = feature
        self.mode = mode
        self.entry = entry
        self.plan_dir = REPO_ROOT / "plans" / feature
        self.feedback_dir = self.plan_dir / "feedback"
        self.progress_file = self.plan_dir / "PROGRESS.md"

        logs = REPO_ROOT / "logs"
        logs.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = logs / f"team-flow-{feature}-{ts}.log"

        self.eventlog = EventLog(feature=feature, base_path=str(REPO_ROOT / "plans"))
        self.state = self.eventlog.reconstruct_state()

    # ── Logging ───────────────────────────────────────────────────────────────

    def log(self, msg: str):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def banner(self, msg: str):
        sep = "═" * 46
        self.log(sep)
        self.log(f"  {msg}")
        self.log(sep)

    # ── FSM ───────────────────────────────────────────────────────────────────

    def emit(self, event) -> State:
        self.eventlog.append(event)
        self.state = reduce(self.state, event)
        self.eventlog.write_state_json(self.state)
        self.log(f"[FSM] {event.type} → {self.state.current}")
        return self.state

    def get_retry_count(self, feedback_file: str) -> int:
        key = f"{self.feature}:{feedback_file}"
        return self.state.retry_count_by_key.get(key, 0)

    def increment_retry(self, feedback_file: str) -> int:
        key = f"{self.feature}:{feedback_file}"
        self.emit(SystemEvent(action="RETRY", metadata={"retry_key": key}))
        return self.state.retry_count_by_key.get(key, 0)

    # ── Subprocess ────────────────────────────────────────────────────────────

    def run_claude(self, prompt: str) -> tuple[int, dict]:
        """Run claude agent. Returns (returncode, usage) where usage may be empty."""
        self.log(">>> Spawning claude agent...")
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", ALLOWED_TOOLS,
             "--output-format", "json"],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True,
        )
        usage = self._parse_usage(result.stdout)
        # Echo stdout so agent output is still visible in the log
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode, usage

    def _parse_usage(self, stdout: str) -> dict:
        """Extract token/cost fields from claude --output-format json stdout."""
        if not stdout:
            return {}
        try:
            data = json.loads(stdout)
            usage = data.get("usage", {})
            return {
                "model":      data.get("model", ""),
                "tokens_in":  usage.get("input_tokens", 0),
                "tokens_out": usage.get("output_tokens", 0),
                "cost_usd":   data.get("cost_usd", 0.0),
            }
        except (json.JSONDecodeError, AttributeError):
            return {}

    # ── Filesystem helpers ────────────────────────────────────────────────────

    def get_feedback_files(self) -> set:
        if not self.feedback_dir.exists():
            return set()
        return {f.name for f in self.feedback_dir.iterdir() if f.suffix == ".md"}

    def check_feedback_changes(self, before: set, after: set):
        for f in after - before:
            self.log(f"[FEEDBACK] Created: {f}")
            self.emit(FileCreatedEvent(file=f))
        for f in before - after:
            self.log(f"[FEEDBACK] Deleted: {f}")
            self.emit(FileDeletedEvent(file=f))

    def get_git_diff(self) -> str:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", ".", ":(exclude)plans/"],
            cwd=str(REPO_ROOT), capture_output=True, text=True,
        )
        return result.stdout

    def git_is_clean(self) -> bool:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT), capture_output=True, text=True,
        )
        return result.stdout.strip() == ""

    def all_conversations_done(self) -> bool:
        if not self.progress_file.exists():
            return False
        return "| TODO |" not in self.progress_file.read_text()

    def plan_files_exist(self) -> list:
        required = [
            "USER_STORIES.md", "IMPLEMENTATION_PLAN.md", "PROGRESS.md",
            "CONVERSATION_PROMPTS.md", "HAPPY_FLOW.md", "EDGE_CASES.md",
            "ARCHITECTURE_PROPOSAL.md", "FLOW_DIAGRAM.md",
        ]
        return [f for f in required if not (self.plan_dir / f).exists()]

    # ── Human input ───────────────────────────────────────────────────────────

    def ask(self, msg: str, options: list) -> str:
        print(f"\n{msg}")
        print(f"  [{' / '.join(options)}]: ", end="", flush=True)
        while True:
            r = input().strip().lower()
            if r in options:
                return r
            print(f"  Enter one of {options}: ", end="", flush=True)

    # ── Agent prompts ─────────────────────────────────────────────────────────

    def p_review(self) -> str:
        return (
            f"You are an adversarial reviewer for the {self.feature} feature.\n\n"
            f"Run: git diff HEAD~1 HEAD\n"
            f"Review changes against:\n"
            f"  - plans/{self.feature}/ARCHITECTURE_PROPOSAL.md\n"
            f"  - plans/{self.feature}/IMPLEMENTATION_PLAN.md\n"
            f"  - .claude/rules/ (if present)\n\n"
            f"Architectural violations → write plans/{self.feature}/feedback/ARCH_FEEDBACK.md:\n"
            f"  [ARCH] <file>:<line> — <violation> — <what it should be>\n\n"
            f"Implementation violations → write plans/{self.feature}/feedback/REVIEW_FAILURES.md:\n"
            f"  [IMPL] <file>:<line> — <violation> — <fix required>\n\n"
            f"If no violations: report PASS. Do NOT write any feedback files."
        )

    def p_fix_arch(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/ARCH_FEEDBACK.md.\n"
            f"Redesign the affected architecture to resolve each [ARCH] item.\n"
            f"Update plans/{self.feature}/ARCHITECTURE_PROPOSAL.md.\n"
            f"If conv scopes need updating, update plans/{self.feature}/IMPLEMENTATION_PLAN.md.\n"
            f"Delete plans/{self.feature}/feedback/ARCH_FEEDBACK.md when resolved.\n"
            f"Report what changed."
        )

    def p_fix_review(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/REVIEW_FAILURES.md.\n"
            f"Step 1 — Apply [AUTO_FIX] patches first (if any):\n"
            f"  For each item tagged [AUTO_FIX], apply the patch exactly as written.\n"
            f"  If a patch fails to apply (line not found), treat it as a regular violation.\n"
            f"Step 2 — Fix remaining regular violations exactly as described.\n"
            f"Do not change anything outside the listed violations.\n"
            f"Delete plans/{self.feature}/feedback/REVIEW_FAILURES.md when all items resolved."
        )

    def p_fix_design(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/DESIGN_QUESTIONS.md.\n"
            f"Resolve each [ARCH] question — update plans/{self.feature}/ARCHITECTURE_PROPOSAL.md.\n"
            f"Delete plans/{self.feature}/feedback/DESIGN_QUESTIONS.md when resolved."
        )

    def p_fix_impl_questions(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/IMPL_QUESTIONS.md.\n"
            f"Answer each [REQ] question — clarify in plans/{self.feature}/USER_STORIES.md "
            f"or plans/{self.feature}/CONVERSATION_PROMPTS.md.\n"
            f"Delete plans/{self.feature}/feedback/IMPL_QUESTIONS.md when resolved."
        )

    def p_test(self) -> str:
        return (
            f"You are a tester verifying the {self.feature} feature.\n\n"
            f"Read plans/{self.feature}/USER_STORIES.md.\n"
            f"For each acceptance criterion: PASS / FAIL / NOT COVERED.\n"
            f"Run verify commands from CONVERSATION_PROMPTS.md where available.\n\n"
            f"Print: | Criterion | Status | Notes |\n\n"
            f"Any FAIL/NOT COVERED → write plans/{self.feature}/feedback/TEST_FAILURES.md:\n"
            f"  [TEST-FAIL] <criterion> — <what is wrong> — <what needs to change>\n\n"
            f"All PASS → report PASS. Do NOT write TEST_FAILURES.md."
        )

    def p_fix_tests(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/TEST_FAILURES.md.\n"
            f"Fix each [TEST-FAIL] item so the criterion is satisfied.\n"
            f"Do not change anything beyond what is needed to pass the listed criteria.\n"
            f"Delete plans/{self.feature}/feedback/TEST_FAILURES.md when resolved."
        )

    # ── Entry skip ────────────────────────────────────────────────────────────

    def skip_to_entry(self):
        """Fast-forward FSM to entry stage when starting fresh (state == IDLE)."""
        if self.state.current != FSMState.IDLE:
            self.log(f"Resuming from existing state: {self.state.current}")
            return

        if self.entry in ("build", "test"):
            missing = self.plan_files_exist()
            if missing:
                print(f"Error: Missing plan files in plans/{self.feature}/: {', '.join(missing)}")
                sys.exit(1)

        if self.entry == "build":
            self.log("[SKIPPED] Discovery + storm + plan → entering at build")
            self._fast_forward_to_building()

        elif self.entry == "test":
            if not self.all_conversations_done():
                print("Error: Not all conversations complete. Run without --entry test first.")
                sys.exit(1)
            self.log("[SKIPPED] Discovery + storm + plan + build → entering at test")
            self._fast_forward_to_building()
            self.emit(ImplementCompleteEvent())  # BUILDING → TESTING

    def _fast_forward_to_building(self):
        """Emit synthetic events to skip storm+plan stages."""
        self.emit(CommandEvent(
            value=f"/team-flow {self.feature}",
            metadata={"feature": self.feature, "mode": self.mode},
        ))
        # IDLE+COMMAND → STORMING
        self.emit(AgentDoneEvent(agent=Agent.ARCHITECT))
        if self.state.current == FSMState.STORM_PAUSED:
            self.emit(HumanResponseEvent(value="yes"))
        # → PLANNING
        self.emit(AgentDoneEvent(agent=Agent.PLANNER))
        if self.state.current == FSMState.PLAN_PAUSED:
            self.emit(HumanResponseEvent(value="go"))
        # → BUILDING

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        if not self._pre_flight():
            return

        if self.state.current == FSMState.IDLE and self.entry == "discovery":
            self.emit(CommandEvent(
                value=f"/team-flow {self.feature}",
                metadata={"feature": self.feature, "mode": self.mode},
            ))
        elif self.entry != "discovery":
            self.skip_to_entry()

        self.banner(f"team-flow: {self.feature}  [mode={self.mode}, entry={self.entry}]")
        self.log(f"Log: {self.log_file}")
        self.log(f"State: {self.state.current}")

        while self.state.current != FSMState.DONE:
            s = self.state.current

            if s == FSMState.STORMING:
                self.banner("STAGE 1 — Storm (architect)")
                self._run_agent(f"/storm {self.feature}", Agent.ARCHITECT, required=True)

            elif s == FSMState.STORM_PAUSED:
                self._pause("Storm complete. Proceed to planning?", "yes", ["yes", "no"],
                            stop_on="no")

            elif s == FSMState.PLANNING:
                self.banner("STAGE 2 — Plan (planner)")
                self._run_agent(f"/plan {self.feature}", Agent.PLANNER, required=True)

            elif s == FSMState.PLAN_PAUSED:
                self._pause("Plan complete. Review plans/ then continue?", "go", ["go", "stop"],
                            stop_on="stop")

            elif s == FSMState.BUILDING:
                self.banner("STAGE 3 — Build (builder)")
                if not self.git_is_clean():
                    self.log("Working directory not clean. Commit or stash first.")
                    self.log(subprocess.run(["git", "status", "--short"],
                                            capture_output=True, text=True,
                                            cwd=str(REPO_ROOT)).stdout)
                    sys.exit(1)
                self._run_agent(f"/build {self.feature} auto", Agent.BUILDER, required=True)

            elif s == FSMState.REVIEWING:
                self.banner("STAGE 3b — Review (reviewer)")
                self._run_agent(self.p_review(), Agent.REVIEWER, required=False)

            elif s == FSMState.IMPLEMENT_PAUSED:
                if self.all_conversations_done():
                    self.log("All conversations complete → testing.")
                    self.emit(ImplementCompleteEvent())
                else:
                    self._pause("Conversation complete + reviewed. Continue to next?",
                                "continue", ["continue", "stop"], stop_on="stop")

            elif s == FSMState.BLOCKED_ON_FEEDBACK:
                self._handle_feedback()

            elif s == FSMState.BLOCKED_ON_HUMAN:
                self._handle_human_block()

            elif s == FSMState.TESTING:
                self.banner("STAGE 4 — Test (tester)")
                self._run_agent(self.p_test(), Agent.TESTER, required=False)

            elif s == FSMState.TEST_PAUSED:
                self._pause("All tests pass. Proceed to retro?", "done", ["done", "fix"],
                            stop_on=None)

            elif s == FSMState.RETRO:
                self.banner("STAGE 5 — Retro (quick)")
                self._run_agent(f"/retro {self.feature}", Agent.QUICK, required=False)

            else:
                self.log(f"Unhandled state: {s}. Stopping.")
                sys.exit(1)

        self.banner(f"DONE — {self.feature}")
        self.log(f"Full log: {self.log_file}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _pre_flight(self) -> bool:
        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("Error: 'claude' CLI not found. Install Claude Code first.")
            return False
        return True

    def _run_agent(self, prompt: str, agent_name: str, required: bool):
        """Run an agent. Emit AGENT_DONE only if no feedback files were created."""
        before = self.get_feedback_files()
        rc, usage = self.run_claude(prompt)
        after = self.get_feedback_files()
        self.check_feedback_changes(before, after)
        if rc != 0 and required:
            self.log(f"Agent {agent_name} failed (exit {rc}). Stopping.")
            sys.exit(1)
        # Don't emit AGENT_DONE if we're now blocked — feedback creation already drove the transition
        if self.state.current not in (FSMState.BLOCKED_ON_FEEDBACK, FSMState.BLOCKED_ON_HUMAN):
            self.emit(AgentDoneEvent(
                agent=agent_name,
                model=usage.get("model", ""),
                tokens_in=usage.get("tokens_in", 0),
                tokens_out=usage.get("tokens_out", 0),
                cost_usd=usage.get("cost_usd", 0.0),
            ))

    def _pause(self, msg: str, fast_response: str, options: list, stop_on: str | None):
        """Pause point: auto-respond in fast mode, else ask human."""
        if self.mode == Mode.FAST:
            self.emit(HumanResponseEvent(value=fast_response))
        else:
            resp = self.ask(f"\n[PAUSE] {msg}", options)
            self.emit(HumanResponseEvent(value=resp))
            if stop_on and resp == stop_on:
                self.log("Stopped at user request.")
                sys.exit(0)

    def _handle_feedback(self):
        open_files = self.get_feedback_files()
        active = next((f for f in FEEDBACK_PRIORITY
                       if f in open_files and f != FeedbackFile.HUMAN_QUESTIONS), None)

        if not active:
            self.log("BLOCKED_ON_FEEDBACK but no feedback files on disk. Recovering...")
            if self.state.active_feedback_file:
                self.emit(FileDeletedEvent(file=self.state.active_feedback_file))
            return

        count = self.increment_retry(active)
        if count > MAX_RETRIES:
            self.log(f"Feedback loop exceeded {MAX_RETRIES} cycles for {active}. Manual intervention required.")
            sys.exit(1)

        self.log(f"Resolving: {active} (attempt {count}/{MAX_RETRIES})")
        before = self.get_feedback_files()

        if active == FeedbackFile.ARCH_FEEDBACK:
            rc, _ = self.run_claude(self.p_fix_arch())
            self.check_feedback_changes(before, self.get_feedback_files())
            if active not in self.get_feedback_files():
                # Arch redesigned — need a full rebuild, not just re-review
                self.emit(StateTransitionEvent(
                    from_state=self.state.current, to_state=FSMState.BUILDING
                ))

        elif active == FeedbackFile.REVIEW_FAILURES:
            diff_before = self.get_git_diff()
            self.run_claude(self.p_fix_review())
            self.check_feedback_changes(before, self.get_feedback_files())
            if self.get_git_diff() == diff_before:
                # Zero-diff stall
                self.log("Zero-diff stall — builder made no changes.")
                self.feedback_dir.mkdir(parents=True, exist_ok=True)
                (self.feedback_dir / FeedbackFile.HUMAN_QUESTIONS).write_text(
                    f"[STALL] Builder and reviewer in zero-diff loop.\n"
                    f"Builder claimed to fix {FeedbackFile.REVIEW_FAILURES} but no code changed.\n"
                    f"Human decision required: accept as-is, override the rule, or rewrite the conv scope.\n"
                )
                self.emit(NoDiffDetectedEvent())
                self.emit(FileCreatedEvent(file=FeedbackFile.HUMAN_QUESTIONS))
                self.log("Written HUMAN_QUESTIONS.md — manual intervention required.")
                sys.exit(1)
            # Re-review after fix
            self._run_agent(self.p_review(), Agent.REVIEWER, required=False)

        elif active == FeedbackFile.DESIGN_QUESTIONS:
            self.run_claude(self.p_fix_design())
            self.check_feedback_changes(before, self.get_feedback_files())

        elif active == FeedbackFile.IMPL_QUESTIONS:
            self.run_claude(self.p_fix_impl_questions())
            self.check_feedback_changes(before, self.get_feedback_files())

        elif active == FeedbackFile.TEST_FAILURES:
            self.run_claude(self.p_fix_tests())
            self.check_feedback_changes(before, self.get_feedback_files())

    def _handle_human_block(self):
        hq = self.feedback_dir / FeedbackFile.HUMAN_QUESTIONS
        if hq.exists():
            print(f"\n{'═'*46}")
            print("HUMAN INTERVENTION REQUIRED")
            print(f"{'═'*46}")
            print(hq.read_text())
            print(f"{'═'*46}")
        print("\nResolve HUMAN_QUESTIONS.md, then press Enter to continue (or type 'quit'): ", end="")
        resp = input().strip().lower()
        if resp == "quit":
            self.log("Stopped at user request.")
            sys.exit(0)
        before = self.get_feedback_files()
        after = self.get_feedback_files()
        self.check_feedback_changes(before, after)
        self.emit(HumanResponseEvent(value="continue"))


def main():
    parser = argparse.ArgumentParser(
        description="FSM-driven pipeline driver for claude-agents-framework"
    )
    parser.add_argument("feature", help="Feature name (plans/<feature>/ must exist for build/test entry)")
    parser.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    parser.add_argument("--fast", action="store_true", help="Skip human pause points")
    parser.add_argument("--recover", action="store_true",
                        help="Reconstruct state from EVENTS.jsonl and resume (default behavior)")
    args = parser.parse_args()

    mode = Mode.FAST if args.fast else Mode.INTERACTIVE
    driver = Driver(feature=args.feature, mode=mode, entry=args.entry)

    if args.recover:
        driver.log(f"Recovered state: {driver.state.current}")

    driver.run()


if __name__ == "__main__":
    main()
