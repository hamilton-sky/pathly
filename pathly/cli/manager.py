"""Candidate CLI manager.

The manager owns parser construction and command dispatch. Command modules own
business behavior, so this file stays mostly wiring.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .agents import ClaudeTextAgent, TextAgent
from .constants import MEET_ALLOWED_ROLES
from .context import ProjectContext
from .help_command import HelpCommand
from .helpers import feature_slug, validate_feature_name
from .hooks_command import HooksCommand
from .installers.codex import CodexInstaller
from .meet_command import MeetCommand
from .menus import MenuPrinter
from orchestrator.constants import Mode
from .plans import PlanRepository
from pathly import team_flow
from pathly.hooks.contracts import HookEvent


class CliManager:
    def __init__(self, agent: TextAgent | None = None):
        self.agent = agent or ClaudeTextAgent()

    def main(self, argv: list[str] | None = None) -> int:
        parser = self.build_parser()
        args = parser.parse_args(argv)
        ctx = ProjectContext.from_args(args)
        plans = PlanRepository(ctx.root)
        menu = MenuPrinter()
        return self.dispatch(args, ctx, plans, menu)

    def dispatch(
        self,
        args: argparse.Namespace,
        ctx: ProjectContext,
        plans: PlanRepository,
        menu: MenuPrinter,
    ) -> int:
        if args.command in {"run", "flow", "team-flow"}:
            return self.run_team_flow(args, ctx.root)
        if args.command == "init":
            plan_dir = plans.create_core_plan(args.feature, force=args.force)
            print(f"Initialized Pathly plan at {plan_dir}")
            return 0
        if args.command == "go":
            return self.run_go(args, ctx.root)
        if args.command == "help":
            return HelpCommand(plans, menu).run(args.feature)
        if args.command == "meet":
            return MeetCommand(plans, menu, self.agent).run(args)
        if args.command == "hooks":
            return HooksCommand().run(args)
        if args.command == "explore":
            return self.run_simple_agent_route(ctx.root, "explore", args.topic, "Question")
        if args.command == "debug":
            return self.run_simple_agent_route(ctx.root, "debug", args.symptom, "Symptom")
        if args.command == "review":
            return self.run_review(ctx.root)
        if args.command == "doctor":
            return self.run_doctor(ctx.root)
        if args.command == "install":
            return self.run_install(args)
        raise AssertionError(args.command)

    def run_team_flow(self, args: argparse.Namespace, root: Path) -> int:
        root.mkdir(parents=True, exist_ok=True)
        team_flow.REPO_ROOT = root

        mode = Mode.FAST if args.fast else Mode.INTERACTIVE
        driver = team_flow.Driver(
            feature=args.feature,
            mode=mode,
            entry=args.entry,
            runner=args.runner,
        )
        if args.recover:
            driver.log(f"Recovered state: {driver.state.current}")
        driver.run()
        return 0

    def run_go(self, args: argparse.Namespace, root: Path) -> int:
        request = " ".join(args.request).strip()
        print("Pathly go")
        print(f"Project: {root}")
        print()
        if not request:
            print("Tell Pathly what you want to build or do.")
            print()
            print("Examples:")
            print("  pathly go add password reset")
            print("  pathly go fix checkout button")
            print("  pathly help")
            return 0

        print(f"Request: {request}")
        print()
        print("Suggested next command:")
        print(f"  pathly flow {feature_slug(request)}")
        return 0

    def run_simple_agent_route(
        self,
        root: Path,
        command: str,
        words: list[str],
        label: str,
    ) -> int:
        topic = " ".join(words).strip()
        print(f"Pathly {command}")
        print(f"Project: {root}")
        if topic:
            print(f"{label}: {topic}")
        print()
        print("Codex/agent workflow:")
        print(f"  Use Pathly to {command} " + (topic or f"<{command}>"))
        print()
        print("CLI fallback:")
        if command == "explore":
            print("  Create an exploration note under explorations/<topic>/, then ask Codex to investigate it.")
        else:
            print("  Capture the symptom, reproduction, root cause, and fix under debugs/<symptom>/.")
        return 0

    def run_review(self, root: Path) -> int:
        print("Pathly review")
        print(f"Project: {root}")
        print()
        print("Codex/agent workflow:")
        print("  Use Pathly review")
        print()
        print("CLI fallback:")
        print("  Run git diff, inspect risks, and record findings before changing code.")
        return 0

    def run_doctor(self, root: Path) -> int:
        ok = True
        print(f"Project: {root}")
        print(f"plans/: {'ok' if (root / 'plans').exists() else 'missing'}")

        claude = shutil.which("claude")
        print(f"claude CLI: {claude or 'missing'}")
        if not claude:
            ok = False

        repo_root = Path(__file__).resolve().parents[2]
        codex_manifest = repo_root / ".codex-plugin" / "plugin.json"
        codex_adapter_manifest = repo_root / "adapters" / "codex" / ".codex-plugin" / "plugin.json"
        print(f"Codex plugin manifest: {'ok' if codex_manifest.exists() else 'missing'}")
        print(
            "Codex adapter manifest: "
            f"{'ok' if codex_adapter_manifest.exists() else 'missing'}"
        )
        return 0 if ok and codex_manifest.exists() and codex_adapter_manifest.exists() else 1

    def run_install(self, args: argparse.Namespace) -> int:
        if args.target == "codex":
            return CodexInstaller(Path(__file__).resolve().parents[2]).run(args)
        if args.target == "claude":
            print("Install Claude Code support from this repository root:")
            print("  ./install.ps1        # Windows")
            print("  bash install.sh      # macOS/Linux")
            return 0
        raise AssertionError(args.target)

    def build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="pathly",
            description="Pathly: guided agent workflows for software changes.",
        )
        parser.add_argument(
            "--project-dir",
            default=".",
            help="Project directory to run Pathly against. Defaults to the current directory.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        self._add_flow_command(subparsers, "run", "Run the Pathly team-flow driver.")
        self._add_flow_command(subparsers, "flow", "Alias for run using Pathly workflow language.")
        self._add_flow_command(subparsers, "team-flow", "Alias for run.")

        init = subparsers.add_parser("init", help="Create starter plan files in a project.")
        init.add_argument("feature", nargs="?", default="demo", type=validate_feature_name, help="Feature name to initialize.")
        init.add_argument("--force", action="store_true", help="Overwrite starter files if they exist.")

        go = subparsers.add_parser("go", help="Suggest the next Pathly workflow for a plain-English request.")
        go.add_argument("request", nargs="*", help="Plain-English request.")

        help_cmd = subparsers.add_parser("help", help="Show project status and suggested next actions.")
        help_cmd.add_argument("feature", nargs="?", type=validate_feature_name, help="Optional feature name under plans/<feature>.")

        meet = subparsers.add_parser("meet", help="Consult one relevant read-only role during an active feature flow.")
        meet.add_argument("feature", nargs="?", type=validate_feature_name, help="Optional feature name under plans/<feature>.")
        meet.add_argument("--role", choices=sorted(MEET_ALLOWED_ROLES), help="Specific role to consult.")
        meet.add_argument("--question", help="Bounded question to ask the consulted role.")
        meet.add_argument(
            "--next",
            dest="next",
            choices=["return", "planner", "architect", "another", "commands", "1", "2", "3", "4", "5"],
            help="Optional follow-up action after the consult note is written.",
        )

        hooks = subparsers.add_parser("hooks", help="Run or configure portable Pathly hooks.")
        hook_actions = hooks.add_subparsers(dest="hooks_action", required=True)
        hook_run = hook_actions.add_parser("run", help="Run a hook event from a JSON payload.")
        hook_run.add_argument("event", choices=[event.value for event in HookEvent])
        hook_run.add_argument("--payload", required=True, help="JSON payload string, fixture path, or '-' for stdin.")

        hook_config = hook_actions.add_parser("print-config", help="Print host hook configuration.")
        hook_config.add_argument("host", choices=["claude", "codex", "cloud"])

        hook_install = hook_actions.add_parser("install", help="Install host hook configuration.")
        hook_install.add_argument("host", choices=["claude"])

        explore = subparsers.add_parser("explore", help="Expose the Pathly exploration workflow.")
        explore.add_argument("topic", nargs="*", help="Question or topic to explore.")

        debug = subparsers.add_parser("debug", help="Expose the Pathly debug workflow.")
        debug.add_argument("symptom", nargs="*", help="Bug symptom to investigate.")

        subparsers.add_parser("review", help="Expose the Pathly review workflow.")
        subparsers.add_parser("doctor", help="Check local Pathly prerequisites.")

        install = subparsers.add_parser("install", help="Show install commands for adapters.")
        install.add_argument("target", choices=["codex", "claude"])
        install.add_argument(
            "--apply",
            action="store_true",
            help="Create the Codex local marketplace files instead of only printing commands.",
        )
        install.add_argument(
            "--market",
            default=r"C:\tmp\pathly-marketplace",
            help="Codex local marketplace directory to create. Defaults to C:\\tmp\\pathly-marketplace.",
        )
        return parser

    def _add_flow_command(
        self,
        subparsers: argparse._SubParsersAction,
        name: str,
        help_text: str,
    ) -> None:
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("feature", type=validate_feature_name, help="Feature name under plans/<feature>.")
        command.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
        command.add_argument("--fast", action="store_true", help="Skip human pause points.")
        command.add_argument("--recover", action="store_true", help="Log reconstructed state before running.")
        command.add_argument(
            "--runner",
            choices=team_flow.RUNNER_CHOICES,
            default=None,
            help=f"Agent runner to use (default: {team_flow.RUNNER_ENV_VAR} or claude).",
        )


def build_parser() -> argparse.ArgumentParser:
    return CliManager().build_parser()


def main(argv: list[str] | None = None) -> int:
    return CliManager().main(argv)
