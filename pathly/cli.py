"""Command-line entry point for Pathly."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
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

    repo_root = Path(__file__).resolve().parents[1]
    codex_manifest = repo_root / ".codex-plugin" / "plugin.json"
    codex_adapter_manifest = repo_root / "adapters" / "codex" / ".codex-plugin" / "plugin.json"
    print(f"Codex plugin manifest: {'ok' if codex_manifest.exists() else 'missing'}")
    print(
        "Codex adapter manifest: "
        f"{'ok' if codex_adapter_manifest.exists() else 'missing'}"
    )
    if not codex_manifest.exists() or not codex_adapter_manifest.exists():
        ok = False

    return 0 if ok else 1


def _codex_marketplace_payload() -> dict:
    return {
        "name": "pathly-local",
        "interface": {"displayName": "Pathly Local"},
        "plugins": [
            {
                "name": "pathly",
                "source": {"source": "local", "path": "./plugins/pathly"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
        ],
    }


def _replace_link_or_empty_dir(path: Path, target: Path) -> None:
    is_junction = getattr(path, "is_junction", lambda: False)
    if path.exists() or path.is_symlink() or is_junction():
        if path.is_symlink() or is_junction():
            path.rmdir()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
        else:
            raise RuntimeError(f"{path} already exists and is not an empty directory or link")

    if os.name == "nt":
        try:
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(path), str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or "").strip()
            raise RuntimeError(f"could not create junction {path} -> {target}: {details}") from exc
    else:
        path.symlink_to(target, target_is_directory=True)


def _install_codex_marketplace(repo_root: Path, market: Path) -> None:
    plugin = market / "plugins" / "pathly"
    manifest_dir = market / ".agents" / "plugins"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    plugin.mkdir(parents=True, exist_ok=True)

    links = {
        ".codex-plugin": repo_root / "adapters" / "codex" / ".codex-plugin",
        "skills": repo_root / "adapters" / "codex" / "skills",
        "core": repo_root / "core",
    }
    for name, target in links.items():
        _replace_link_or_empty_dir(plugin / name, target)

    marketplace_path = manifest_dir / "marketplace.json"
    marketplace_path.write_text(
        json.dumps(_codex_marketplace_payload(), indent=2) + "\n",
        encoding="utf-8",
    )


def _plan_dirs(root: Path) -> list[Path]:
    plans_dir = root / "plans"
    if not plans_dir.exists():
        return []
    return sorted(
        (path for path in plans_dir.iterdir() if path.is_dir() and path.name != ".archive"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


STANDARD_PLAN_FILES = {
    "HAPPY_FLOW.md",
    "EDGE_CASES.md",
    "ARCHITECTURE_PROPOSAL.md",
    "FLOW_DIAGRAM.md",
}


def _infer_rigor(plan: Path | None) -> str:
    if plan is None or not plan.exists():
        return "unknown"
    if (plan / "STATE.json").exists() and (plan / "EVENTS.jsonl").exists():
        return "strict"

    files = {path.name for path in plan.iterdir() if path.is_file()}
    if STANDARD_PLAN_FILES <= files:
        return "standard"
    return "lite"


def _progress_counts(plan: Path) -> tuple[int, int, int]:
    progress = plan / "PROGRESS.md"
    if not progress.exists():
        return 0, 0, 0

    done = 0
    todo = 0
    active = 0
    for line in progress.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped or "Conversation" in stripped:
            continue

        cells = [cell.strip().lower() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue

        status = cells[-1]
        if status in {"done", "complete", "completed"}:
            done += 1
        elif status in {"in_progress", "in progress", "active", "building"}:
            active += 1
        elif status:
            todo += 1

    return done, todo, active


def _has_open_feedback(plan: Path) -> bool:
    feedback = plan / "feedback"
    return feedback.exists() and any(path.is_file() for path in feedback.iterdir())


def _print_banner(lines: list[str]) -> None:
    rule = "=" * 43
    print(rule)
    for line in lines:
        print(f"  {line}")
    print(rule)


def _print_no_feature_menu() -> None:
    _print_banner(["Pathly", "No active feature found"])
    print()
    print("  What do you want to do?")
    print()
    print("  [1] Brainstorm/refine an unclear idea       -> storm")
    print("  [2] Describe what you want (plain English)  -> director")
    print("  [3] Start a new feature (full pipeline)     -> team-flow")
    print("  [4] Start a new feature with a PRD/BMAD file")
    print("  [5] See all commands")
    print()
    print("Reply with 1, 2, 3, 4, or 5:")


def _print_build_done_menu(feature: str, rigor: str) -> None:
    _print_banner([f"{feature} - All conversations complete", f"Rigor: {rigor}"])
    print()
    print("  What do you want to do?")
    print()
    print("  [1] Run tests                 -> tester verifies all ACs")
    print("  [2] Run tests + retro         -> full finish")
    print(f"  [3] Write retro only          -> retro {feature}")
    print("  [4] See all commands")
    print()
    print("Reply with 1-4:")


def _print_plan_done_menu(feature: str, rigor: str, done: int, remaining: int) -> None:
    _print_banner(
        [
            f"{feature} - Plan ready",
            f"Conv: {done} done . {remaining} remaining",
            f"Rigor: {rigor}",
        ]
    )
    print()
    print("  What do you want to do?")
    print()
    print("  [1] Continue building         -> next TODO conversation")
    print("  [2] Run full pipeline         -> build + review + test + retro")
    print("  [3] Run full pipeline (fast)  -> no pause points")
    print("  [4] Review current code       -> review")
    print("  [5] Change rigor              -> see options")
    print("  [6] See all commands")
    print()
    print("Reply with 1-6:")


def _print_feedback_menu(feature: str, rigor: str, plan: Path) -> None:
    _print_banner([f"{feature} - Open feedback requires action", f"Rigor: {rigor}"])
    print()
    print("  Open files:")
    feedback = plan / "feedback"
    for path in sorted(feedback.iterdir()):
        if path.is_file():
            print(f"    {path.name}")
    print()
    print("  What do you want to do?")
    print()
    print("  [1] Resume pipeline (routes to correct agent automatically)")
    print("  [2] See the feedback file contents")
    print("  [3] See all commands")
    print()
    print("Reply with 1, 2, or 3:")


def _print_retro_done_menu(feature: str, rigor: str) -> None:
    _print_banner([f"{feature} - DONE", "RETRO.md written", f"Rigor: {rigor}"])
    print()
    print("  What do you want to do?")
    print()
    print("  [1] Archive this feature      -> moves to plans/.archive/")
    print("  [2] Promote lessons           -> lessons")
    print("  [3] Start next feature        -> team-flow <new-feature>")
    print("  [4] Read the retro            -> show RETRO.md")
    print("  [5] See all commands")
    print()
    print("Reply with 1-5:")


def cmd_help(args: argparse.Namespace) -> int:
    root = _project_root(args)
    plans = _plan_dirs(root)

    if not plans:
        _print_no_feature_menu()
        return 0

    plan = root / "plans" / args.feature if args.feature else plans[0]
    if not plan.exists():
        _print_no_feature_menu()
        return 0

    feature = plan.name
    rigor = _infer_rigor(plan)

    if _has_open_feedback(plan):
        _print_feedback_menu(feature, rigor, plan)
        return 0

    if (plan / "RETRO.md").exists():
        _print_retro_done_menu(feature, rigor)
        return 0

    done, todo, active = _progress_counts(plan)
    remaining = todo + active
    if remaining:
        _print_plan_done_menu(feature, rigor, done, remaining)
        return 0

    _print_build_done_menu(feature, rigor)
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    if args.target == "codex":
        repo_root = Path(__file__).resolve().parents[1]
        market = Path(args.market).expanduser().resolve()
        if args.apply:
            try:
                _install_codex_marketplace(repo_root, market)
            except RuntimeError as exc:
                print(f"Could not install Codex marketplace: {exc}")
                print("Remove or rename that path, then run this command again.")
                return 1

            print(f"Installed Pathly Codex marketplace at {market}")
            print()
            print("Next:")
            print(f"  codex plugin marketplace add {market}")
            print("  Restart Codex, then use: Use Pathly help")
            return 0

        print("Install the Codex plugin through a local marketplace:")
        print()
        print("  python -m pip install -e .")
        print(f"  pathly install codex --apply --market \"{market}\"")
        print("  codex plugin marketplace add " + str(market))
        print()
        print("Manual PowerShell setup:")
        print()
        print(f"  $market = \"{market}\"")
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
        print("Restart Codex after adding or changing the local marketplace.")
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
    install.set_defaults(func=cmd_install)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
