"""Command-line entry point for Pathly."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from orchestrator.constants import Mode
from scripts import team_flow


CORE_PLAN_FILES = {
    "USER_STORIES.md": "# User Stories\n\n",
    "IMPLEMENTATION_PLAN.md": "# Implementation Plan\n\n",
    "PROGRESS.md": "# Progress\n\n| Conversation | Status |\n|---|---|\n",
    "CONVERSATION_PROMPTS.md": "# Conversation Prompts\n\n",
}


def _project_root(args: argparse.Namespace) -> Path:
    return Path(args.project_dir).expanduser().resolve()


def cmd_run(args: argparse.Namespace) -> int:
    root = _project_root(args)
    root.mkdir(parents=True, exist_ok=True)
    team_flow.REPO_ROOT = root

    mode = Mode.FAST if args.fast else Mode.INTERACTIVE
    driver = team_flow.Driver(feature=args.feature, mode=mode, entry=args.entry)
    if args.recover:
        driver.log(f"Recovered state: {driver.state.current}")
    driver.run()
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    root = _project_root(args)
    plan_dir = root / "plans" / args.feature
    plan_dir.mkdir(parents=True, exist_ok=True)
    for name, content in CORE_PLAN_FILES.items():
        path = plan_dir / name
        if not path.exists() or args.force:
            path.write_text(content, encoding="utf-8")
    print(f"Initialized Pathly plan at {plan_dir}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = _project_root(args)
    ok = True

    print(f"Project: {root}")
    print(f"plans/: {'ok' if (root / 'plans').exists() else 'missing'}")

    claude = shutil.which("claude")
    print(f"claude CLI: {claude or 'missing'}")
    if not claude:
        ok = False

    codex_manifest = Path(__file__).resolve().parents[1] / ".codex-plugin" / "plugin.json"
    print(f"Codex plugin manifest: {'ok' if codex_manifest.exists() else 'missing'}")
    if not codex_manifest.exists():
        ok = False

    return 0 if ok else 1


def cmd_install(args: argparse.Namespace) -> int:
    if args.target == "codex":
        print("Install the Codex plugin from this repository root:")
        print("  codex plugin marketplace add <path-to-pathly-repo>")
        print("  codex plugin marketplace upgrade pathly")
        return 0
    if args.target == "claude":
        print("Install Claude Code support from this repository root:")
        print("  ./install.ps1        # Windows")
        print("  bash install.sh      # macOS/Linux")
        return 0
    raise AssertionError(args.target)


def build_parser() -> argparse.ArgumentParser:
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

    run = subparsers.add_parser("run", help="Run the Pathly team-flow driver.")
    run.add_argument("feature", help="Feature name under plans/<feature>.")
    run.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    run.add_argument("--fast", action="store_true", help="Skip human pause points.")
    run.add_argument("--recover", action="store_true", help="Log reconstructed state before running.")
    run.set_defaults(func=cmd_run)

    team = subparsers.add_parser("team-flow", help="Alias for run.")
    team.add_argument("feature", help="Feature name under plans/<feature>.")
    team.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    team.add_argument("--fast", action="store_true", help="Skip human pause points.")
    team.add_argument("--recover", action="store_true", help="Log reconstructed state before running.")
    team.set_defaults(func=cmd_run)

    init = subparsers.add_parser("init", help="Create starter plan files in a project.")
    init.add_argument("feature", nargs="?", default="demo", help="Feature name to initialize.")
    init.add_argument("--force", action="store_true", help="Overwrite starter files if they exist.")
    init.set_defaults(func=cmd_init)

    doctor = subparsers.add_parser("doctor", help="Check local Pathly prerequisites.")
    doctor.set_defaults(func=cmd_doctor)

    install = subparsers.add_parser("install", help="Show install commands for adapters.")
    install.add_argument("target", choices=["codex", "claude"])
    install.set_defaults(func=cmd_install)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
