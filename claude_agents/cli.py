import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

_PKG = Path(__file__).parent
DATA_DIR = _PKG / "data"
ORCHESTRATOR_DIR = _PKG / "orchestrator"


def cmd_install(dry_run=False):
    claude_dir = Path.home() / ".claude"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = claude_dir / f".backup-{timestamp}"

    # Backup existing agents/skills if present
    needs_backup = (claude_dir / "agents").exists() or (claude_dir / "skills").exists()
    if needs_backup and not dry_run:
        print(f"Backing up existing files to {backup_dir} ...")
        backup_dir.mkdir(parents=True, exist_ok=True)
        for d in ("agents", "skills", "templates"):
            src = claude_dir / d
            if src.exists():
                shutil.copytree(src, backup_dir / d)

    # (src_dir, dest_relative_to_claude_dir)
    # dest "." means files go directly into ~/.claude/ (used for docs)
    copies = [
        (DATA_DIR / "agents",    "agents"),
        (DATA_DIR / "skills",    "skills"),
        (DATA_DIR / "templates", "templates"),
        (DATA_DIR / "docs",      "."),
        (DATA_DIR / "hooks",     "hooks"),
        (ORCHESTRATOR_DIR,       "orchestrator"),
    ]

    for src_dir, rel_dest in copies:
        if not src_dir.exists():
            print(f"  [skip] {src_dir} not found", file=sys.stderr)
            continue
        dest_root = claude_dir if rel_dest == "." else claude_dir / rel_dest
        for src_file in sorted(src_dir.rglob("*")):
            if not src_file.is_file():
                continue
            if "__pycache__" in src_file.parts or src_file.suffix == ".pyc":
                continue
            if src_file.name == "test_fsm.py":
                continue  # don't deploy tests to ~/.claude
            rel = src_file.relative_to(src_dir)
            if rel_dest == ".":
                dst = claude_dir / src_file.name
            else:
                dst = dest_root / rel
            if dry_run:
                print(f"  [dry-run] {src_file} -> {dst}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst)
                print(f"  {dst}")

    if not dry_run:
        _merge_settings(claude_dir)

    print("\nInstall complete." if not dry_run else "\nDry run complete — no files written.")
    if not dry_run:
        print("Open any project in Claude Code and run: /go <what you want to build>")


def _merge_settings(claude_dir: Path):
    settings_file = claude_dir / "settings.json"
    hook_cmd = "python ~/.claude/hooks/classify_feedback.py"
    hook_entry = {
        "matcher": "Write",
        "hooks": [{"type": "command", "command": hook_cmd}],
    }
    settings: dict = {}
    if settings_file.exists():
        with open(settings_file) as f:
            settings = json.load(f)

    existing = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])
    already = any(
        h.get("matcher") == "Write"
        and any("classify_feedback.py" in hh.get("command", "") for hh in h.get("hooks", []))
        for h in existing
    )
    if not already:
        existing.append(hook_entry)
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        print("  Hook config added to settings.json")
    else:
        print("  Hook config already present — skipped")


def main():
    parser = argparse.ArgumentParser(
        prog="claude-agents",
        description="Claude Agents Framework — install agents, skills, and templates into ~/.claude/",
    )
    sub = parser.add_subparsers(dest="command")

    install_p = sub.add_parser("install", help="Install framework files into ~/.claude/")
    install_p.add_argument("--dry-run", action="store_true", help="Preview without writing files")

    args = parser.parse_args()
    if args.command == "install":
        cmd_install(dry_run=getattr(args, "dry_run", False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
