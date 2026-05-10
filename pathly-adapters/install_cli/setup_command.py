import argparse
import sys
from pathlib import Path

import yaml

from .detect import detect_hosts
from .resources import adapter_meta_path, adapter_install_yaml, core_agents_path
from .stitch import stitch_agent
from .materialize import materialize


def _load_install_yaml(host: str) -> dict:
    install_path = adapter_install_yaml(host)
    if not install_path.exists():
        raise FileNotFoundError(f"No install.yaml for host {host!r}: {install_path}")
    with open(install_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _run_host(host: str, dry_run: bool, repair: bool, force: bool) -> None:
    install_cfg = _load_install_yaml(host)
    dest = Path(install_cfg["destination"]).expanduser()

    meta_dir = adapter_meta_path(host)
    core_dir = core_agents_path()

    agent_files: dict[str, str] = {}
    for meta_file in sorted(meta_dir.glob("*.yaml")):
        if meta_file.name == "install.yaml":
            continue
        agent_name = meta_file.stem
        core_file = core_dir / f"{agent_name}.md"
        if not core_file.exists():
            print(f"  [warn] No core file for {agent_name!r}, skipping", file=sys.stderr)
            continue
        agent_files[f"{agent_name}.md"] = stitch_agent(core_file, meta_file)

    if dry_run:
        print(f"\n[{host}] Would write to {dest}:")
        for name in sorted(agent_files):
            print(f"  {dest / name}")
        return

    written = materialize(agent_files, dest, repair=repair, force=force, dry_run=False)
    if written:
        print(f"[{host}] Wrote {len(written)} file(s) to {dest}")
    else:
        print(f"[{host}] Nothing to write (files already current or not Pathly-owned)")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pathly-setup",
        description="Stitch and install Pathly agent files into AI host tools.",
    )
    parser.add_argument(
        "host", nargs="?",
        help="Target host (claude, codex, copilot). Defaults to all detected.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview writes without touching the filesystem.")
    parser.add_argument("--apply", action="store_true", help="Write agent files to host config locations.")
    parser.add_argument("--repair", action="store_true", help="Overwrite Pathly-owned files.")
    parser.add_argument("--force", action="store_true", help="Overwrite all files, even those not owned by Pathly.")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("pathly-setup: no writes performed (pass --apply to install, --dry-run to preview).")
        detected = detect_hosts()
        if detected:
            print(f"Detected hosts: {', '.join(detected)}")
        else:
            print("No supported hosts detected.")
        return

    hosts = [args.host] if args.host else detect_hosts()
    if not hosts:
        print("No supported hosts detected. Install Claude Code, Codex, or VS Code + Copilot first.")
        sys.exit(1)

    failed = False
    for host in hosts:
        try:
            _run_host(host, dry_run=args.dry_run, repair=args.repair, force=args.force)
        except Exception as e:
            print(f"[{host}] Error: {e}", file=sys.stderr)
            failed = True

    if failed:
        sys.exit(1)
