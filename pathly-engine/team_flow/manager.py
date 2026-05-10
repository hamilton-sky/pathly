"""Candidate team-flow manager.

This keeps the FSM loop in one coordinator while moving prompts, filesystem
access, logging, and configuration out to focused collaborators.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .config import DriverConfig, MAX_RETRIES
from .filesystem import TeamFlowFiles
from .flow_logging import DriverLogger
from orchestrator.constants import Agent, FeedbackFile, FSMState, Mode
from orchestrator.eventlog import EventLog
from orchestrator.events import (
    AgentDoneEvent,
    CommandEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    HumanResponseEvent,
    ImplementCompleteEvent,
    NoDiffDetectedEvent,
    StateTransitionEvent,
    SystemEvent,
)
from orchestrator.feedback import highest_priority_feedback
from orchestrator.reducer import reduce
from orchestrator.state import State
from pathly.runners import ClaudeRunner, CodexRunner, Runner
from .prompts import PromptFactory


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ENV_VAR = "PATHLY_RUNNER"
RUNNER_CHOICES = ("claude", "codex", "auto")


class TeamFlowDriver:
    def __init__(
        self,
        feature: str,
        mode: str,
        entry: str,
        repo_root: Path | None = None,
        runner: str | Runner | None = None,
    ):
        self.config = DriverConfig(
            repo_root=(repo_root or REPO_ROOT),
            feature=feature,
            mode=mode,
            entry=entry,
        )
        self.feature = feature
        self.mode = mode
        self.entry = entry
        self.plan_dir = self.config.plan_dir
        self.feedback_dir = self.config.feedback_dir
        self.progress_file = self.config.progress_file

        self.logger = DriverLogger(self.config.repo_root, feature)
        self.files = TeamFlowFiles(self.config)
        self.prompts = PromptFactory(feature)
        self.eventlog = EventLog(feature=feature, base_path=str(self.config.repo_root / "plans"))
        self.state = self.eventlog.reconstruct_state()
        self.runner = self._select_runner(runner)

    @property
    def log_file(self) -> Path:
        return self.logger.log_file

    def log(self, message: str) -> None:
        self.logger.log(message)

    def banner(self, message: str) -> None:
        self.logger.banner(message)

    def emit(self, event) -> State:
        self.eventlog.append(event)
        self.state = reduce(self.state, event)
        self.eventlog.write_state_json(self.state)
        self.log(f"[FSM] {event.type} -> {self.state.current}")
        return self.state

    def run_claude(self, prompt: str) -> tuple[int, dict]:
        result = self.runner.run(prompt)
        return result.return_code, result.usage

    def _select_runner(self, requested: str | Runner | None) -> Runner:
        if requested and not isinstance(requested, str):
            return requested

        selected = (requested or os.environ.get(RUNNER_ENV_VAR) or "claude").lower()
        if selected not in RUNNER_CHOICES:
            raise ValueError(f"Unsupported runner '{selected}'. Choose one of: {', '.join(RUNNER_CHOICES)}")

        if selected == "auto":
            claude = ClaudeRunner(
                repo_root=self.config.repo_root,
                log=self.log,
                on_timeout=self._handle_agent_timeout,
            )
            if claude.is_available():
                return claude
            return CodexRunner(
                repo_root=self.config.repo_root,
                log=self.log,
                on_timeout=self._handle_agent_timeout,
            )

        if selected == "claude":
            return ClaudeRunner(
                repo_root=self.config.repo_root,
                log=self.log,
                on_timeout=self._handle_agent_timeout,
            )
        return CodexRunner(
            repo_root=self.config.repo_root,
            log=self.log,
            on_timeout=self._handle_agent_timeout,
        )

    def _handle_agent_timeout(self, timeout: int) -> None:
        self.emit(SystemEvent(action="TIMEOUT", metadata={"timeout_seconds": timeout}))

    def get_feedback_files(self) -> set:
        return self.files.feedback_files()

    def check_feedback_changes(self, before: set, after: set) -> None:
        for file_name in after - before:
            self.log(f"[FEEDBACK] Created: {file_name}")
            self.emit(FileCreatedEvent(file=file_name))
        for file_name in before - after:
            self.log(f"[FEEDBACK] Deleted: {file_name}")
            self.emit(FileDeletedEvent(file=file_name))

    def get_git_diff(self) -> str:
        return self.files.git_diff()

    def git_is_clean(self) -> bool:
        return self.files.git_is_clean()

    def all_conversations_done(self) -> bool:
        return self.files.all_conversations_done()

    def plan_files_exist(self) -> list[str]:
        return self.files.missing_core_plan_files()

    def ask(self, message: str, options: list[str]) -> str:
        print(f"\n{message}")
        print(f"  [{' / '.join(options)}]: ", end="", flush=True)
        while True:
            response = input().strip().lower()
            if response in options:
                return response
            print(f"  Enter one of {options}: ", end="", flush=True)

    def skip_to_entry(self) -> None:
        if self.state.current != FSMState.IDLE:
            self.log(f"Resuming from existing state: {self.state.current}")
            return

        if self.entry in ("build", "test"):
            missing = self.plan_files_exist()
            if missing:
                print(f"Error: Missing plan files in plans/{self.feature}/: {', '.join(missing)}")
                sys.exit(1)

        if self.entry == "build":
            self.log("[SKIPPED] Discovery + storm + plan -> entering at build")
            self._fast_forward_to_building()
        elif self.entry == "test":
            if not self.all_conversations_done():
                print("Error: Not all conversations complete. Run without --entry test first.")
                sys.exit(1)
            self.log("[SKIPPED] Discovery + storm + plan + build -> entering at test")
            self._fast_forward_to_building()
            self.emit(ImplementCompleteEvent())

    def run(self) -> None:
        if not self._pre_flight():
            return

        self._startup_verify()
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
            self._process_current_state()

        self.banner(f"DONE - {self.feature}")
        self.log(f"Full log: {self.log_file}")

    def _process_current_state(self) -> None:
        state = self.state.current
        if state == FSMState.STORMING:
            self.banner("STAGE 1 - Storm (architect)")
            self._run_agent(self.prompts.storm(), Agent.ARCHITECT, required=True)
        elif state == FSMState.STORM_PAUSED:
            self._pause("Storm complete. Proceed to planning?", "yes", ["yes", "no"], stop_on="no")
        elif state == FSMState.PLANNING:
            self.banner("STAGE 2 - Plan (planner)")
            self._run_agent(self.prompts.plan(), Agent.PLANNER, required=True)
        elif state == FSMState.PLAN_PAUSED:
            self._pause("Plan complete. Review plans/ then continue?", "go", ["go", "stop"], stop_on="stop")
        elif state == FSMState.BUILDING:
            self._run_building_state()
        elif state == FSMState.REVIEWING:
            self.banner("STAGE 3b - Review (reviewer)")
            self._run_agent(self.prompts.review(), Agent.REVIEWER, required=False)
        elif state == FSMState.IMPLEMENT_PAUSED:
            self._handle_implement_pause()
        elif state == FSMState.BLOCKED_ON_FEEDBACK:
            self._handle_feedback()
        elif state == FSMState.BLOCKED_ON_HUMAN:
            self._handle_human_block()
        elif state == FSMState.TESTING:
            self.banner("STAGE 4 - Test (tester)")
            self._run_agent(self.prompts.test(), Agent.TESTER, required=False)
        elif state == FSMState.TEST_PAUSED:
            self._pause("All tests pass. Proceed to retro?", "done", ["done", "fix"], stop_on=None)
        elif state == FSMState.RETRO:
            self.banner("STAGE 5 - Retro (quick)")
            self._run_agent(self.prompts.retro(), Agent.QUICK, required=False)
        else:
            self.log(f"Unhandled state: {state}. Stopping.")
            sys.exit(1)

    def _run_building_state(self) -> None:
        self.banner("STAGE 3 - Build (builder)")
        if not self.git_is_clean():
            self.log("Working directory not clean. Commit or stash first.")
            status = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=str(self.config.repo_root),
            )
            self.log(status.stdout)
            sys.exit(1)
        self._run_agent(self.prompts.build(), Agent.BUILDER, required=True)

    def _handle_implement_pause(self) -> None:
        if self.all_conversations_done():
            self.log("All conversations complete -> testing.")
            self.emit(ImplementCompleteEvent())
            return
        self._pause(
            "Conversation complete + reviewed. Continue to next?",
            "continue",
            ["continue", "stop"],
            stop_on="stop",
        )

    def _startup_verify(self) -> None:
        issues = []
        safe_deletes = []

        if self.feedback_dir.exists():
            known_event_ids = self.files.event_ids(self.plan_dir / "EVENTS.jsonl")
            for feedback_file in self.feedback_dir.glob("*.md"):
                reason = self.files.feedback_ttl_issue(feedback_file, known_event_ids)
                if reason:
                    safe_deletes.append((feedback_file, reason))

        if self.state.current == FSMState.BUILDING and self.progress_file.exists():
            content = self.progress_file.read_text(encoding="utf-8")
            if "in progress" not in content.lower():
                issues.append(
                    "STATE.json says BUILDING but no conversation is marked in_progress "
                    f"in PROGRESS.md. Suggestion: run /team-flow {self.feature} build to resync."
                )

        if not issues and not safe_deletes:
            return

        if self.mode == Mode.FAST:
            for path, reason in safe_deletes:
                path.unlink()
                self.log(f"[FSM AUTO] Removed orphan: {path.name} ({reason})")
            if issues:
                print("\n" + "=" * 46)
                print("  [STARTUP] Real issues found - fast mode cannot auto-resolve:")
                for index, issue in enumerate(issues, 1):
                    print(f"  {index}. {issue}")
                print("  Run /help --doctor for details and fix options.")
                print("=" * 46 + "\n")
                sys.exit(1)
            return

        print("\n" + "=" * 46)
        print(f"  [STARTUP CHECK] - {self.feature}")
        print(f"  {len(safe_deletes) + len(issues)} issue(s) found before pipeline starts")
        print("=" * 46)

        for path, reason in safe_deletes:
            print(f"\n  Orphan/expired: {path.name}")
            print(f"  Why: {reason}")
            print("  Action: will delete before continuing")
        for issue in issues:
            print(f"\n  Issue: {issue}")

        print()
        if safe_deletes:
            answer = input("  Delete orphan file(s) and continue? [yes / no]: ").strip().lower()
            if answer != "yes":
                print("  Aborted. Run /help --doctor for full diagnostics.")
                sys.exit(0)
            for path, _ in safe_deletes:
                path.unlink()
                self.log(f"[STARTUP] Removed orphan: {path.name}")

        if issues:
            answer = input("  Real issues remain. Continue anyway? [yes / no]: ").strip().lower()
            if answer != "yes":
                print("  Aborted. Run /help --doctor for full diagnostics.")
                sys.exit(0)

    def _pre_flight(self) -> bool:
        if not self.runner.is_available():
            print(f"Error: '{self.runner.name}' CLI not found. Install {self.runner.name} first.")
            return False
        return True

    def _run_agent(self, prompt: str, agent_name: str, required: bool) -> None:
        before = self.get_feedback_files()
        return_code, usage = self.run_claude(prompt)
        after = self.get_feedback_files()
        self.check_feedback_changes(before, after)
        if return_code != 0 and required:
            self.log(f"Agent {agent_name} failed (exit {return_code}). Stopping.")
            sys.exit(1)
        if self.state.current not in (FSMState.BLOCKED_ON_FEEDBACK, FSMState.BLOCKED_ON_HUMAN):
            self.emit(AgentDoneEvent(
                agent=agent_name,
                model=usage.get("model", ""),
                tokens_in=usage.get("tokens_in", 0),
                tokens_out=usage.get("tokens_out", 0),
                cost_usd=usage.get("cost_usd", 0.0),
            ))

    def _pause(self, message: str, fast_response: str, options: list[str], stop_on: str | None) -> None:
        if self.mode == Mode.FAST:
            self.emit(HumanResponseEvent(value=fast_response))
            return

        response = self.ask(f"\n[PAUSE] {message}", options)
        self.emit(HumanResponseEvent(value=response))
        if stop_on and response == stop_on:
            self.log("Stopped at user request.")
            sys.exit(0)

    def _handle_feedback(self) -> None:
        open_files = self.get_feedback_files()
        active = highest_priority_feedback(open_files, include_human=False)
        if not active:
            self.log("BLOCKED_ON_FEEDBACK but no feedback files on disk. Recovering...")
            if self.state.active_feedback_file:
                self.emit(FileDeletedEvent(file=self.state.active_feedback_file))
            return

        count = self._increment_retry(active)
        if count > MAX_RETRIES:
            self.log(f"Feedback loop exceeded {MAX_RETRIES} cycles for {active}. Manual intervention required.")
            sys.exit(1)

        self.log(f"Resolving: {active} (attempt {count}/{MAX_RETRIES})")
        before = self.get_feedback_files()

        if active == FeedbackFile.ARCH_FEEDBACK:
            self.run_claude(self.prompts.fix_arch())
            self.check_feedback_changes(before, self.get_feedback_files())
            if active not in self.get_feedback_files():
                self.emit(StateTransitionEvent(from_state=self.state.current, to_state=FSMState.BUILDING))
        elif active == FeedbackFile.REVIEW_FAILURES:
            self._handle_review_failure(before, active)
        elif active == FeedbackFile.DESIGN_QUESTIONS:
            self.run_claude(self.prompts.fix_design())
            self.check_feedback_changes(before, self.get_feedback_files())
        elif active == FeedbackFile.IMPL_QUESTIONS:
            self.run_claude(self.prompts.fix_impl_questions())
            self.check_feedback_changes(before, self.get_feedback_files())
        elif active == FeedbackFile.TEST_FAILURES:
            self.run_claude(self.prompts.fix_tests())
            self.check_feedback_changes(before, self.get_feedback_files())

    def _handle_review_failure(self, before: set, active: str) -> None:
        diff_before = self.get_git_diff()
        self.run_claude(self.prompts.fix_review())
        self.check_feedback_changes(before, self.get_feedback_files())
        if self.get_git_diff() == diff_before:
            self.log("Zero-diff stall - builder made no changes.")
            self.feedback_dir.mkdir(parents=True, exist_ok=True)
            (self.feedback_dir / FeedbackFile.HUMAN_QUESTIONS).write_text(
                f"[STALL] Builder and reviewer in zero-diff loop.\n"
                f"Builder claimed to fix {FeedbackFile.REVIEW_FAILURES} but no code changed.\n"
                "Human decision required: accept as-is, override the rule, or rewrite the conv scope.\n",
                encoding="utf-8",
            )
            self.emit(NoDiffDetectedEvent())
            self.emit(FileCreatedEvent(file=FeedbackFile.HUMAN_QUESTIONS))
            self.log("Written HUMAN_QUESTIONS.md - manual intervention required.")
            sys.exit(1)
        if active not in self.get_feedback_files():
            self._run_agent(self.prompts.review(), Agent.REVIEWER, required=False)

    def _handle_human_block(self) -> None:
        questions = self.feedback_dir / FeedbackFile.HUMAN_QUESTIONS
        if questions.exists():
            print("\n" + "=" * 46)
            print("HUMAN INTERVENTION REQUIRED")
            print("=" * 46)
            print(questions.read_text(encoding="utf-8"))
            print("=" * 46)
        before = self.get_feedback_files()
        print("\nResolve HUMAN_QUESTIONS.md, then press Enter to continue (or type 'quit'): ", end="")
        response = input().strip().lower()
        if response == "quit":
            self.log("Stopped at user request.")
            sys.exit(0)
        self.check_feedback_changes(before, self.get_feedback_files())
        self.emit(HumanResponseEvent(value="continue"))

    def _fast_forward_to_building(self) -> None:
        self.emit(CommandEvent(
            value=f"/team-flow {self.feature}",
            metadata={"feature": self.feature, "mode": self.mode},
        ))
        self.emit(AgentDoneEvent(agent=Agent.ARCHITECT))
        if self.state.current == FSMState.STORM_PAUSED:
            self.emit(HumanResponseEvent(value="yes"))
        self.emit(AgentDoneEvent(agent=Agent.PLANNER))
        if self.state.current == FSMState.PLAN_PAUSED:
            self.emit(HumanResponseEvent(value="go"))

    def _increment_retry(self, feedback_file: str) -> int:
        key = f"{self.feature}:{feedback_file}"
        self.emit(SystemEvent(action="RETRY", metadata={"retry_key": key}))
        return self.state.retry_count_by_key.get(key, 0)


Driver = TeamFlowDriver


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FSM-driven pipeline driver for Pathly")
    parser.add_argument("feature", help="Feature name (plans/<feature>/ must exist for build/test entry)")
    parser.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    parser.add_argument("--fast", action="store_true", help="Skip human pause points")
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Reconstruct state from EVENTS.jsonl and resume (default behavior)",
    )
    parser.add_argument(
        "--runner",
        choices=RUNNER_CHOICES,
        default=None,
        help=f"Agent runner to use (default: {RUNNER_ENV_VAR} or claude)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    mode = Mode.FAST if args.fast else Mode.INTERACTIVE
    driver = TeamFlowDriver(feature=args.feature, mode=mode, entry=args.entry, runner=args.runner)
    if args.recover:
        driver.log(f"Recovered state: {driver.state.current}")
    driver.run()
