"""Codex marketplace installer for the candidate CLI."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


class CodexInstaller:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def run(self, args) -> int:
        market = Path(args.market).expanduser().resolve()
        if args.apply:
            try:
                self.install_marketplace(market)
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

        self.print_instructions(market)
        return 0

    def install_marketplace(self, market: Path) -> None:
        plugin = market / "plugins" / "pathly"
        manifest_dir = market / ".agents" / "plugins"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        plugin.mkdir(parents=True, exist_ok=True)

        links = {
            ".codex-plugin": self.repo_root / "adapters" / "codex" / ".codex-plugin",
            "skills": self.repo_root / "adapters" / "codex" / "skills",
            "core": self.repo_root / "core",
        }
        for name, target in links.items():
            replace_link_or_empty_dir(plugin / name, target)

        (manifest_dir / "marketplace.json").write_text(
            json.dumps(codex_marketplace_payload(), indent=2) + "\n",
            encoding="utf-8",
        )

    def print_instructions(self, market: Path) -> None:
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
        print(f"  New-Item -ItemType Junction -Path \"$plugin\\.codex-plugin\" -Target \"{self.repo_root}\\adapters\\codex\\.codex-plugin\"")
        print(f"  New-Item -ItemType Junction -Path \"$plugin\\skills\" -Target \"{self.repo_root}\\adapters\\codex\\skills\"")
        print(f"  New-Item -ItemType Junction -Path \"$plugin\\core\" -Target \"{self.repo_root}\\core\"")
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


def codex_marketplace_payload() -> dict:
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


def replace_link_or_empty_dir(path: Path, target: Path) -> None:
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
