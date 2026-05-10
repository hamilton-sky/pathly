import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _find_plans_dir() -> Path:
    here = Path.cwd()
    for candidate in [here, *here.parents]:
        p = candidate / "plans"
        if p.is_dir():
            return p
    return Path.cwd() / "plans"


def _active_feature_dir(plans: Path, feature: str | None) -> Path | None:
    if feature:
        d = plans / feature
        return d if d.is_dir() else None
    candidates = sorted(
        plans.glob("*/STATE.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0].parent if candidates else None


def _read_state(feature_dir: Path) -> dict:
    state_file = feature_dir / "STATE.json"
    if not state_file.exists():
        return {}
    with state_file.open() as f:
        return json.load(f)


def _suggest_next(state: dict) -> str:
    current = state.get("current", "IDLE")
    blocked_on = state.get("active_feedback_file", "feedback file")
    table = {
        "IDLE": "Run /pathly start <feature> in Claude Code to begin a new feature.",
        "PO_DISCUSSING": "PO discussion in progress. Open Claude Code to continue.",
        "PO_PAUSED": "Resume PO discussion: open Claude Code and run /po to continue.",
        "EXPLORING": "Exploration in progress. Wait for discoverer agent to finish.",
        "EXPLORE_PAUSED": "Resume explore: open Claude Code and run /explore to continue.",
        "STORMING": "Storm in progress. Open Claude Code to continue.",
        "STORM_PAUSED": "Resume storm: open Claude Code and run /storm to continue.",
        "PLANNING": "Planning in progress. Open Claude Code to continue.",
        "PLAN_PAUSED": "Resume plan: open Claude Code and run /plan to continue.",
        "BUILDING": "Build in progress. Open Claude Code and run /build to continue.",
        "REVIEWING": "Reviewing in progress. Wait for reviewer agent to finish.",
        "IMPLEMENT_PAUSED": "Build paused. Check REVIEW_FAILURES.md and run /build to resume.",
        "TESTING": "Testing in progress. Wait for tester agent to finish.",
        "TEST_PAUSED": "Tests paused. Check TEST_FAILURES.md and run /build to resume.",
        "RETRO": "Run /retro in Claude Code to complete the retrospective.",
        "BLOCKED_ON_FEEDBACK": f"Blocked. Resolve {blocked_on} then run /build in Claude Code.",
        "BLOCKED_ON_HUMAN": "Blocked. Answer HUMAN_QUESTIONS.md then run /build in Claude Code.",
        "DONE": "Feature complete. Run /retro if not done, or start a new feature.",
    }
    return table.get(current, f"State: {current}. Open Claude Code to continue.")


def _append_event(feature_dir: Path, event_type: str, metadata: dict) -> None:
    events_file = feature_dir / "EVENTS.jsonl"
    event = {
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
    }
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def cmd_go(intent: str) -> None:
    plans = _find_plans_dir()
    feature_dir = _active_feature_dir(plans, None)
    if feature_dir is None:
        print("No active feature found. Run /pathly start <feature> in Claude Code.")
        sys.exit(1)
    state = _read_state(feature_dir)
    feature = state.get("active_feature") or feature_dir.name
    _append_event(feature_dir, "COMMAND", {"value": intent, "source": "pathly-go"})
    print(f"Feature: {feature}")
    print(f"State:   {state.get('current', 'IDLE')}")
    print(f"Intent:  {intent}")
    print()
    print(_suggest_next(state))


def cmd_status(feature: str | None = None) -> None:
    plans = _find_plans_dir()
    feature_dir = _active_feature_dir(plans, feature)
    if feature_dir is None:
        msg = f"Feature '{feature}' not found in plans/." if feature else "No active feature found in plans/."
        print(msg)
        sys.exit(1)
    state = _read_state(feature_dir)
    feature_name = feature or state.get("active_feature") or feature_dir.name
    print(f"Feature:     {feature_name}")
    print(f"State:       {state.get('current', 'IDLE')}")
    print(f"Rigor:       {state.get('rigor', '-')}")
    print(f"Last actor:  {state.get('last_actor', '-')}")
    print(f"Events:      {state.get('event_count', 0)}")
    print(f"Updated:     {state.get('updated_at', '-')}")
    print()
    print(_suggest_next(state))


def cmd_doctor() -> None:
    checks: list[tuple[str, bool, str]] = []

    try:
        import engine_cli  # noqa: F401
        checks.append(("engine installed", True, ""))
    except ImportError as e:
        checks.append(("engine installed", False, str(e)))

    plans = _find_plans_dir()
    if plans.is_dir():
        checks.append(("plans/ accessible", True, str(plans)))
    else:
        checks.append(("plans/ accessible", False, f"not found at {plans}"))

    feature_dir = _active_feature_dir(plans, None)
    if feature_dir is not None:
        state_file = feature_dir / "STATE.json"
        try:
            with state_file.open() as f:
                json.load(f)
            checks.append(("STATE.json readable", True, str(state_file)))
        except Exception as e:
            checks.append(("STATE.json readable", False, str(e)))
    else:
        checks.append(("STATE.json readable", False, "no feature with STATE.json found"))

    if feature_dir is not None:
        events_file = feature_dir / "EVENTS.jsonl"
        if events_file.exists():
            try:
                with events_file.open() as f:
                    for line in f:
                        if line.strip():
                            json.loads(line)
                checks.append(("EVENTS.jsonl readable", True, str(events_file)))
            except Exception as e:
                checks.append(("EVENTS.jsonl readable", False, str(e)))
        else:
            checks.append(("EVENTS.jsonl readable", False, f"not found at {events_file}"))
    else:
        checks.append(("EVENTS.jsonl readable", False, "no feature directory found"))

    for label, ok, detail in checks:
        icon = "PASS" if ok else "FAIL"
        line = f"  [{icon}]  {label}"
        if detail:
            line += f"  ({detail})"
        print(line)

    print()
    failed = [c for c in checks if not c[1]]
    if failed:
        print(f"{len(failed)} check(s) failed.")
        sys.exit(1)
    else:
        print("All checks passed.")
