"""Smoke tests for public plugin packaging and README commands."""

import json
import re
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_plugin_manifests_parse_and_point_to_skills():
    """Claude and Codex manifests should stay valid as branding changes."""
    for manifest_path in [
        REPO_ROOT / ".claude-plugin" / "plugin.json",
        REPO_ROOT / ".codex-plugin" / "plugin.json",
    ]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["name"] == "pathly"
        assert manifest["version"]
        assert manifest["skills"].strip("./") == "skills"
        assert (REPO_ROOT / "skills").is_dir()


def test_python_distribution_is_pathly():
    """The Python distribution name should match the product name."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["name"] == "pathly"


def test_claude_install_paths_use_pathly_plugin_dir():
    """Installers should install runtime plugin files under the Pathly name."""
    install_sh = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    install_ps1 = (REPO_ROOT / "install.ps1").read_text(encoding="utf-8")
    setup_hook_sh = (REPO_ROOT / "scripts" / "setup-hook.sh").read_text(encoding="utf-8")
    setup_hook_ps1 = (REPO_ROOT / "scripts" / "setup-hook.ps1").read_text(encoding="utf-8")

    assert 'PLUGIN_NAME="pathly"' in install_sh
    assert '$PluginName = "pathly"' in install_ps1
    assert "plugins/pathly" in setup_hook_sh
    assert "plugins\\pathly" in setup_hook_ps1


def test_readme_slash_commands_map_to_skills():
    """Documented slash commands should not drift from the skill folders."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"^/([a-z][a-z-]*)(?=\s|$)", readme, re.MULTILINE))
    skill_names = {path.name for path in (REPO_ROOT / "skills").iterdir() if path.is_dir()}

    # These commands are the new-user front door and should always be real.
    assert {"go", "help", "debug", "explore"}.issubset(documented)
    assert documented <= skill_names
