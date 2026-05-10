"""Install-time agent stitcher.

Combines a host-neutral core agent contract with a platform-specific meta YAML
to produce a complete agent file for the target host.
"""

from __future__ import annotations

from pathlib import Path

import yaml


_FRONTMATTER_KEYS = ("name", "description", "model", "tools", "skills")


def stitch_agent(core_path: Path, meta_path: Path) -> str:
    """Read core agent md + meta YAML, return complete stitched agent file content."""
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))

    lines: list[str] = ["---"]
    for key in _FRONTMATTER_KEYS:
        if key not in meta:
            continue
        value = meta[key]
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")

    can_spawn = meta.get("can_spawn", [])
    lines.append("## Capabilities")
    if can_spawn == "all":
        lines.append("This agent may spawn any other agent type.")
    elif not can_spawn:
        lines.append("TERMINAL — this agent may not spawn sub-agents.")
    else:
        lines.append(f"This agent may spawn: {', '.join(str(a) for a in can_spawn)}.")
    lines.append("")

    lines.append(core_path.read_text(encoding="utf-8").rstrip("\n"))
    lines.append("")

    spawn_section = (meta.get("spawn_section") or "").rstrip("\n")
    if spawn_section:
        lines.append(spawn_section)
        lines.append("")

    return "\n".join(lines)
