"""Host-neutral package resource API for Pathly packaged assets.

Provides a single point for loading core prompts, role contracts, templates,
and adapter assets from an installed wheel without repo-root assumptions.

Uses importlib.resources semantics where the package is available, with a
fallback to Path(__file__) for editable installs.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterator


_PACKAGE_ROOT = Path(__file__).parent
_REPO_ROOT = _PACKAGE_ROOT.parent


def _asset_root() -> Path:
    """Return the root from which packaged assets are resolved.

    In a source checkout the repo root owns core/ and adapters/.
    In an installed wheel the data-files land relative to the package root.
    We prefer the repo root when it is present; otherwise fall back to the
    installed data location under the package root.
    """
    if (_REPO_ROOT / "core").is_dir():
        return _REPO_ROOT
    installed = _PACKAGE_ROOT / "core"
    if installed.is_dir():
        return _PACKAGE_ROOT
    raise FileNotFoundError(
        "Pathly packaged assets not found. "
        "Run 'pip install pathly' or install from source."
    )


def core_prompt(name: str) -> Path:
    """Return the path to a core skill file.

    Args:
        name: Skill name without extension (e.g. 'plan', 'help', 'go').

    Returns:
        Resolved Path to the skill file.

    Raises:
        FileNotFoundError: If the skill does not exist in the package.
    """
    root = _asset_root()
    path = root / "core" / "skills" / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Core skill not found: core/skills/{name}.md")
    return path


def core_agent(name: str) -> Path:
    """Return the path to a core agent contract file.

    Args:
        name: Agent filename with extension (e.g. 'builder.md').

    Returns:
        Resolved Path to the agent contract file.

    Raises:
        FileNotFoundError: If the agent contract does not exist.
    """
    root = _asset_root()
    path = root / "core" / "agents" / name
    if not path.exists():
        raise FileNotFoundError(f"Core agent contract not found: core/agents/{name}")
    return path


def core_template(name: str) -> Path:
    """Return the path to a core plan template file.

    Args:
        name: Template filename with extension (e.g. 'PROGRESS.template.md').

    Returns:
        Resolved Path to the template file.

    Raises:
        FileNotFoundError: If the template does not exist.
    """
    root = _asset_root()
    path = root / "core" / "templates" / "plan" / name
    if not path.exists():
        raise FileNotFoundError(f"Core template not found: core/templates/plan/{name}")
    return path


def adapter_asset(adapter: str, *parts: str) -> Path:
    """Return the path to an adapter asset.

    Args:
        adapter: Adapter name (e.g. 'claude-code', 'codex', 'cli').
        *parts: Path components relative to the adapter directory.

    Returns:
        Resolved Path to the adapter asset.

    Raises:
        FileNotFoundError: If the adapter asset does not exist.
    """
    root = _asset_root()
    path = root / "adapters" / adapter / Path(*parts)
    if not path.exists():
        raise FileNotFoundError(
            f"Adapter asset not found: adapters/{adapter}/{'/'.join(parts)}"
        )
    return path


def list_core_prompts() -> list[Path]:
    """Return all core skill files.

    Returns:
        Sorted list of Paths to core skill files.
    """
    root = _asset_root()
    skills_dir = root / "core" / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(skills_dir.glob("*.md"))


def list_core_agents() -> list[Path]:
    """Return all core agent contract files (excluding README).

    Returns:
        Sorted list of Paths to agent contract files.
    """
    root = _asset_root()
    agents_dir = root / "core" / "agents"
    if not agents_dir.is_dir():
        return []
    return sorted(p for p in agents_dir.glob("*.md") if p.name != "README.md")


def list_adapter_agents(adapter: str) -> list[Path]:
    """Return all agent files for an adapter.

    Args:
        adapter: Adapter name (e.g. 'claude', 'codex', 'copilot').

    Returns:
        Sorted list of Paths to agent files (excluding README).
    """
    root = _asset_root()
    agents_dir = root / "adapters" / adapter / "agents"
    if not agents_dir.is_dir():
        return []
    return sorted(p for p in agents_dir.glob("*.md") if p.name != "README.md")


def copy_asset(src: Path, dest: Path) -> None:
    """Copy a packaged asset to a destination path, preserving relative structure.

    Args:
        src: Source path (from a resource helper like core_prompt or adapter_asset).
        dest: Destination path. Parent directories are created as needed.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_asset_tree(src_dir: Path, dest_dir: Path) -> None:
    """Recursively copy a packaged asset directory to a destination.

    Args:
        src_dir: Source directory (must exist).
        dest_dir: Destination directory. Created if it does not exist.
    """
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)


def package_version() -> str:
    """Return the installed Pathly package version.

    Prefers importlib.metadata for installed packages and falls back to the
    __version__ attribute defined in pathly/__init__.py for editable installs.

    Returns:
        Version string (e.g. '2.0.0').
    """
    try:
        from importlib.metadata import version, PackageNotFoundError
        try:
            return version("pathly")
        except PackageNotFoundError:
            pass
    except ImportError:
        pass

    import pathly
    return getattr(pathly, "__version__", "unknown")
