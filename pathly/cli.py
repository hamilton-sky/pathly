"""Command-line entry point for Pathly."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from orchestrator.constants import Mode
from scripts import team_flow


CORE_PLAN_FILES = {
    "USER_STORIES.md": "# User Stories\n\n",
    "IMPLEMENTATION_PLAN.md": "# Implementation Plan\n\n",
    "PROGRESS.md": "# Progress\n\n| Conversation | Status |\n|---|---|\n",
    "CONVERSATION_PROMPTS.md": "# Conversation Prompts\n\n",
}


FEATURE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
PROMOTION_TARGET_RE = re.compile(
    r"^## Promotion Target\s*(?:\r?\n)+([A-Za-z-]+)\s*$",
    re.MULTILINE,
)

MEET_ALLOWED_ROLES = {
    "planner": "requirements, stories, acceptance criteria, task breakdown",
    "architect": "design, layers, contracts, migrations, rollback",
    "reviewer": "review risks, contract violations, diff quality",
    "tester": "verification strategy, acceptance coverage, likely gaps",
    "po": "product scope, user value, success criteria, epic boundaries",
    "scout": "read-only codebase investigation",
}

MEET_ROLE_SETS = {
    "planning": ["planner", "po", "architect"],
    "building": ["planner", "architect", "reviewer", "tester", "scout"],
    "review feedback open": ["reviewer", "architect", "planner", "scout"],
    "architecture feedback open": ["architect", "planner", "reviewer", "scout"],
    "testing": ["tester", "planner", "architect", "reviewer", "scout"],
    "done / retro complete": ["reviewer", "tester", "planner"],
}

READ_ONLY_TOOLS = "Read,Glob,Grep,Agent"
PLAN_WRITE_TOOLS = "Read,Glob,Grep,Write,Edit,Agent"

def _project_root(args: argparse.Namespace) -> Path:
    return Path(args.project_dir).expanduser().resolve()


def _validate_feature_name(value: str) -> str:
    if not FEATURE_NAME_RE.fullmatch(value) or ".." in value:
        raise argparse.ArgumentTypeError(
            "feature must be 1-80 chars: letters, numbers, dots, underscores, or hyphens; no path segments"
        )
    return value


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


def _run_claude_text(prompt: str, *, cwd: Path, allowed_tools: str, timeout: int | None = None) -> str:
    timeout = timeout or int(os.environ.get("CLAUDE_AGENT_TIMEOUT", "1800"))
    result = subprocess.run(
        ["claude", "-p", prompt, "--allowedTools", allowed_tools],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "claude consultation failed").strip()
        raise RuntimeError(details)
    return result.stdout.strip()


def _select_plan(root: Path, feature: str | None) -> Path | None:
    if feature:
        plan = root / "plans" / feature
        return plan if plan.exists() else None
    plans = _plan_dirs(root)
    return plans[0] if plans else None


def _infer_meet_state(plan: Path) -> str:
    feedback = plan / "feedback"
    if feedback.exists():
        files = {path.name for path in feedback.iterdir() if path.is_file()}
        if "ARCH_FEEDBACK.md" in files or "DESIGN_QUESTIONS.md" in files:
            return "architecture feedback open"
        if files:
            return "review feedback open"
    if (plan / "RETRO.md").exists():
        return "done / retro complete"
    done, todo, active = _progress_counts(plan)
    if active or todo:
        return "building"
    if done:
        return "testing"
    return "planning"


def _relevant_meet_roles(state: str) -> list[str]:
    return list(MEET_ROLE_SETS.get(state, ["planner", "architect", "reviewer", "tester", "scout"]))


def _prompt_choice(prompt: str, options: list[str]) -> str:
    print(prompt)
    while True:
        answer = input().strip().lower()
        if answer in options:
            return answer
        print(f"Reply with one of: {', '.join(options)}")


def _print_meet_menu(feature: str, state: str, roles: list[str]) -> None:
    _print_banner([f"meet - {feature}", f"State: {state}"])
    print()
    print("  Pick a role to consult:")
    print()
    for index, role in enumerate(roles, start=1):
        print(f"  [{index}] {role:<12} -> {MEET_ALLOWED_ROLES[role]}")
    print(f"  [{len(roles) + 1}] See all commands")
    print()
    print(f"Reply with 1-{len(roles) + 1}:")


def _consult_note_path(plan: Path, role: str) -> Path:
    consults = plan / "consults"
    consults.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return consults / f"{timestamp}-{role}.md"


def _parse_promotion_target(answer: str) -> str:
    match = PROMOTION_TARGET_RE.search(answer)
    if not match:
        return "none"
    value = match.group(1).strip().lower()
    if value not in {"none", "planner", "architect"}:
        return "none"
    return value


def _meet_prompt(feature: str, role: str, question: str, note_path: Path) -> str:
    role_brief = MEET_ALLOWED_ROLES[role]
    return f"""You are acting as Pathly's {role} advisor for the active feature '{feature}'.

This is a read-only consultation. You may read the project and spawn read-only subagents if needed, but you must not edit code, edit plan files, delete feedback files, or claim the workflow has advanced.

Question: {question}

Focus area: {role_brief}

Answer in this exact markdown shape:
# Meet Note - {role} - {feature}

## Question
{question}

## Answer
<direct answer>

## Evidence
- <file, pattern, or reason 1>
- <file, pattern, or reason 2>

## Recommendation
<what the user should do next>

## Promotion Target
<none|planner|architect>

Choose planner only if the answer should change stories, acceptance criteria, ordering, or task decomposition.
Choose architect only if the answer should change design, contracts, layers, rollback, or integration shape.
Choose none if the answer is advisory only.

Do not wrap the answer in code fences. The note will be written to {note_path} by the CLI runtime."""


def _promotion_prompt(feature: str, role: str, note_path: Path) -> str:
    if role == "planner":
        scope = (
            f"Read {note_path}. Update only the plan files directly affected by the consult note in plans/{feature}/. "
            "You may edit USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, and CONVERSATION_PROMPTS.md if warranted. "
            "Do not edit source code. Report exactly what changed."
        )
    else:
        scope = (
            f"Read {note_path}. Update only architecture-related plan files directly affected by the consult note in plans/{feature}/. "
            "You may edit ARCHITECTURE_PROPOSAL.md, FLOW_DIAGRAM.md, or IMPLEMENTATION_PLAN.md if warranted. "
            "Do not edit source code. Report exactly what changed."
        )
    return scope


def _return_route_for_state(feature: str, state: str) -> str:
    if state == "testing":
        return f"team-flow {feature} test"
    if state in {"review feedback open", "architecture feedback open"}:
        return f"team-flow {feature} build"
    if state == "done / retro complete":
        return f"help {feature}"
    return f"team-flow {feature} build"


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


def cmd_meet(args: argparse.Namespace) -> int:
    root = _project_root(args)
    plan = _select_plan(root, args.feature)
    if plan is None:
        print("meet requires an active feature plan. Start a feature first, then run meet again.")
        return 1

    if not shutil.which("claude"):
        print("meet requires the claude CLI for read-only role consultation.")
        return 1

    feature = plan.name
    state = _infer_meet_state(plan)
    roles = _relevant_meet_roles(state)
    role = args.role.lower() if args.role else None
    if role and role not in roles:
        print(f"Role '{role}' is not available for meet in state: {state}")
        return 1

    if role is None:
        _print_meet_menu(feature, state, roles)
        choice = _prompt_choice("", [str(i) for i in range(1, len(roles) + 2)])
        if choice == str(len(roles) + 1):
            print("Use `pathly help` to see the full command reference.")
            return 0
        role = roles[int(choice) - 1]

    question = args.question.strip() if args.question else ""
    if not question:
        question = input(f"What is the one question you want to ask {role}? ").strip()
    if not question:
        print("meet requires a non-empty question.")
        return 1

    note_path = _consult_note_path(plan, role)
    answer = _run_claude_text(
        _meet_prompt(feature, role, question, note_path),
        cwd=root,
        allowed_tools=READ_ONLY_TOOLS,
    )
    note_path.write_text(answer + "\n", encoding="utf-8")
    promotion_target = _parse_promotion_target(answer)

    print(f"Meet note written: {note_path}")
    print(f"Suggested promotion target: {promotion_target}")
    print()
    print("What do you want to do next?")
    print()
    print(f"[1] Return to {_return_route_for_state(feature, state)}")
    print("[2] Promote to planner update")
    print("[3] Promote to architecture update")
    print("[4] Ask another meet question")
    print("[5] See all commands")
    print()

    next_choice = args.next
    if next_choice is None:
        next_choice = _prompt_choice("Reply with 1-5:", ["1", "2", "3", "4", "5"])
    else:
        next_choice = next_choice.lower()

    if next_choice in {"1", "return"}:
        print(f"Return route: {_return_route_for_state(feature, state)}")
        return 0

    if next_choice in {"2", "planner"}:
        result = _run_claude_text(
            _promotion_prompt(feature, "planner", note_path),
            cwd=root,
            allowed_tools=PLAN_WRITE_TOOLS,
        )
        print(result)
        return 0

    if next_choice in {"3", "architect"}:
        result = _run_claude_text(
            _promotion_prompt(feature, "architect", note_path),
            cwd=root,
            allowed_tools=PLAN_WRITE_TOOLS,
        )
        print(result)
        return 0

    if next_choice in {"4", "another"}:
        follow_up = argparse.Namespace(
            project_dir=str(root),
            feature=feature,
            role=None,
            question=None,
            next=None,
        )
        return cmd_meet(follow_up)

    print("Use `pathly help` to see the full command reference.")
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
    print("  [5] Meet a role               -> meet <feature>")
    print("  [6] Change rigor              -> see options")
    print("  [7] See all commands")
    print()
    print("Reply with 1-7:")


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
    run.add_argument("feature", type=_validate_feature_name, help="Feature name under plans/<feature>.")
    run.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    run.add_argument("--fast", action="store_true", help="Skip human pause points.")
    run.add_argument("--recover", action="store_true", help="Log reconstructed state before running.")
    run.set_defaults(func=cmd_run)

    flow = subparsers.add_parser("flow", help="Alias for run using Pathly workflow language.")
    flow.add_argument("feature", type=_validate_feature_name, help="Feature name under plans/<feature>.")
    flow.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    flow.add_argument("--fast", action="store_true", help="Skip human pause points.")
    flow.add_argument("--recover", action="store_true", help="Log reconstructed state before running.")
    flow.set_defaults(func=cmd_run)

    team = subparsers.add_parser("team-flow", help="Alias for run.")
    team.add_argument("feature", type=_validate_feature_name, help="Feature name under plans/<feature>.")
    team.add_argument("--entry", choices=["discovery", "build", "test"], default="discovery")
    team.add_argument("--fast", action="store_true", help="Skip human pause points.")
    team.add_argument("--recover", action="store_true", help="Log reconstructed state before running.")
    team.set_defaults(func=cmd_run)

    init = subparsers.add_parser("init", help="Create starter plan files in a project.")
    init.add_argument("feature", nargs="?", default="demo", type=_validate_feature_name, help="Feature name to initialize.")
    init.add_argument("--force", action="store_true", help="Overwrite starter files if they exist.")
    init.set_defaults(func=cmd_init)

    go = subparsers.add_parser("go", help="Suggest the next Pathly workflow for a plain-English request.")
    go.add_argument("request", nargs="*", help="Plain-English request.")
    go.set_defaults(func=cmd_go)

    help_cmd = subparsers.add_parser("help", help="Show project status and suggested next actions.")
    help_cmd.add_argument("feature", nargs="?", type=_validate_feature_name, help="Optional feature name under plans/<feature>.")
    help_cmd.set_defaults(func=cmd_help)

    meet = subparsers.add_parser("meet", help="Consult one relevant read-only role during an active feature flow.")
    meet.add_argument("feature", nargs="?", type=_validate_feature_name, help="Optional feature name under plans/<feature>.")
    meet.add_argument("--role", choices=sorted(MEET_ALLOWED_ROLES), help="Specific role to consult.")
    meet.add_argument("--question", help="Bounded question to ask the consulted role.")
    meet.add_argument(
        "--next",
        dest="next",
        choices=["return", "planner", "architect", "another", "commands", "1", "2", "3", "4", "5"],
        help="Optional follow-up action after the consult note is written.",
    )
    meet.set_defaults(func=cmd_meet)

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
