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


def _feature_slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    parts = [part for part in slug.split("-") if part]
    return "-".join(parts[:6]) or "demo"


def cmd_go(args: argparse.Namespace) -> int:
    root = _project_root(args)
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

    feature = _feature_slug(request)
    print(f"Request: {request}")
    print()
    print("Suggested next command:")
    print(f"  pathly flow {feature}")
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


def cmd_explore(args: argparse.Namespace) -> int:
    root = _project_root(args)
    topic = " ".join(args.topic).strip()

    print("Pathly explore")
    print(f"Project: {root}")
    if topic:
        print(f"Question: {topic}")
    print()
    print("Codex/agent workflow:")
    print("  Use Pathly to explore " + (topic or "<question>"))
    print()
    print("CLI fallback:")
    print("  Create an exploration note under explorations/<topic>/, then ask Codex to investigate it.")
    return 0


def cmd_debug(args: argparse.Namespace) -> int:
    root = _project_root(args)
    symptom = " ".join(args.symptom).strip()

    print("Pathly debug")
    print(f"Project: {root}")
    if symptom:
        print(f"Symptom: {symptom}")
    print()
    print("Codex/agent workflow:")
    print("  Use Pathly to debug " + (symptom or "<symptom>"))
    print()
    print("CLI fallback:")
    print("  Capture the symptom, reproduction, root cause, and fix under debugs/<symptom>/.")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    root = _project_root(args)

    print("Pathly review")
    print(f"Project: {root}")
    print()
    print("Codex/agent workflow:")
    print("  Use Pathly review")
    print()
    print("CLI fallback:")
    print("  Run git diff, inspect risks, and record findings before changing code.")
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


def _plan_dirs(root: Path) -> list[Path]:
    plans_dir = root / "plans"
    if not plans_dir.exists():
        return []
    return sorted(
        (path for path in plans_dir.iterdir() if path.is_dir() and path.name != ".archive"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def cmd_help(args: argparse.Namespace) -> int:
    root = _project_root(args)
    plans = _plan_dirs(root)

    print("Pathly help")
    print(f"Project: {root}")
    print(f"plans/: {'ok' if plans else 'missing'}")
    print()

    if not plans:
        print("No active Pathly plans found.")
        print()
        print("Next:")
        print("  pathly init <feature>        Create starter plan files")
        print("  pathly doctor                Check local setup")
        return 0

    print("Plans:")
    for plan in plans[:5]:
        progress = plan / "PROGRESS.md"
        status = "has PROGRESS.md" if progress.exists() else "missing PROGRESS.md"
        print(f"  {plan.name}: {status}")

    feature = args.feature or plans[0].name
    print()
    print("Next:")
    print(f"  pathly run {feature} --entry discovery")
    print(f"  pathly run {feature} --entry build")
    print(f"  pathly run {feature} --entry test")
    print("  pathly doctor")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    if args.target == "codex":
        repo_root = Path(__file__).resolve().parents[1]
        print("Install the Codex plugin through a local marketplace:")
        print()
        print("  python -m pip install -e .")
        print("  $market = \"C:\\tmp\\pathly-marketplace\"")
        print("  $plugin = \"$market\\plugins\\pathly\"")
        print("  New-Item -ItemType Directory -Path \"$market\\.agents\\plugins\" -Force")
        print("  New-Item -ItemType Directory -Path \"$plugin\" -Force")
        print(f"  New-Item -ItemType Junction -Path \"$plugin\\.codex-plugin\" -Target \"{repo_root}\\adapters\\codex\\.codex-plugin\"")
        print(f"  New-Item -ItemType Junction -Path \"$plugin\\skills\" -Target \"{repo_root}\\adapters\\codex\\skills\"")
        print(f"  New-Item -ItemType Junction -Path \"$plugin\\core\" -Target \"{repo_root}\\core\"")
        print("  @'")
        print("  {")
        print("    \"name\": \"pathly-local\",")
        print("    \"interface\": { \"displayName\": \"Pathly Local\" },")
        print("    \"plugins\": [")
        print("      {")
        print("        \"name\": \"pathly\",")
        print("        \"source\": { \"source\": \"local\", \"path\": \"./plugins/pathly\" },")
        print("        \"policy\": { \"installation\": \"AVAILABLE\", \"authentication\": \"ON_INSTALL\" },")
        print("        \"category\": \"Developer Tools\"")
        print("      }")
        print("    ]")
        print("  }")
        print("  '@ | Set-Content \"$market\\.agents\\plugins\\marketplace.json\"")
        print("  codex plugin marketplace add $market")
        print()
        print("This registers Pathly for Codex globally on this machine. Each user")
        print("still needs their own local clone or installed copy of this repo.")
        print()
        print("If PowerShell cannot find codex, run the same command with the full")
        print("codex.exe path from your Codex or ChatGPT VS Code extension.")
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

    flow = subparsers.add_parser("flow", help="Alias for run using Pathly workflow language.")
    flow.add_argument("feature", help="Feature name under plans/<feature>.")
    flow.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    flow.add_argument("--fast", action="store_true", help="Skip human pause points.")
    flow.add_argument("--recover", action="store_true", help="Log reconstructed state before running.")
    flow.set_defaults(func=cmd_run)

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

    go = subparsers.add_parser("go", help="Suggest the next Pathly workflow for a plain-English request.")
    go.add_argument("request", nargs="*", help="Plain-English request.")
    go.set_defaults(func=cmd_go)

    help_cmd = subparsers.add_parser("help", help="Show project status and suggested next actions.")
    help_cmd.add_argument("feature", nargs="?", help="Optional feature name under plans/<feature>.")
    help_cmd.set_defaults(func=cmd_help)

    explore = subparsers.add_parser("explore", help="Expose the Pathly exploration workflow.")
    explore.add_argument("topic", nargs="*", help="Question or topic to explore.")
    explore.set_defaults(func=cmd_explore)

    debug = subparsers.add_parser("debug", help="Expose the Pathly debug workflow.")
    debug.add_argument("symptom", nargs="*", help="Bug symptom to investigate.")
    debug.set_defaults(func=cmd_debug)

    review = subparsers.add_parser("review", help="Expose the Pathly review workflow.")
    review.set_defaults(func=cmd_review)

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
