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
    assert pyproject["project"]["scripts"]["pathly"] == "pathly.cli:main"
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["include"] == [
        "orchestrator*",
        "pathly*",
        "scripts*",
    ]


def test_orchestrator_stays_top_level_runtime_package():
    """The Python FSM runtime should not be absorbed into core content files."""
    assert (REPO_ROOT / "orchestrator" / "__init__.py").exists()
    assert (REPO_ROOT / "orchestrator" / "reducer.py").exists()
    assert not (REPO_ROOT / "core" / "orchestrator").exists()


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
    """Documented Pathly commands should not drift from the skill folders."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    skill_names = {path.name for path in (REPO_ROOT / "skills").iterdir() if path.is_dir()}

    # These slash-command entry points are the new-user front doors.
    documented_entrypoints = set(re.findall(r"/(pathly|path)(?=\s|$)", readme))
    assert {"pathly", "path"}.issubset(documented_entrypoints)
    assert documented_entrypoints <= skill_names

    # The README intentionally namespaces user-facing commands under /pathly.
    documented_pathly_commands = set(re.findall(r"/pathly\s+([a-z][a-z-]*)(?=\s|$)", readme))
    assert {"help", "doctor", "debug", "explore", "flow", "review"}.issubset(
        documented_pathly_commands
    )

    # The core skill table should only list real root skills.
    documented_skill_rows = set(re.findall(r"^\| `([a-z][a-z-]*)` \| `/pathly", readme, re.MULTILINE))
    assert documented_skill_rows
    assert documented_skill_rows <= skill_names


def test_skills_are_core_backed_wrappers():
    """Live slash-command skills should point at canonical core prompts."""
    skill_dirs = [path for path in (REPO_ROOT / "skills").iterdir() if path.is_dir()]

    assert skill_dirs
    for skill_dir in skill_dirs:
        skill = skill_dir.name
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        core_prompt = REPO_ROOT / "core" / "prompts" / f"{skill}.md"

        assert core_prompt.exists(), f"Missing core prompt for {skill}"
        assert f"core/prompts/{skill}.md" in skill_text
        assert "adapter-facing wrapper" in skill_text


def test_core_agent_contracts_exist_for_live_agents():
    """Core should own host-neutral copies of the agent contracts."""
    live_agents = {
        path.name
        for path in (REPO_ROOT / "agents").glob("*.md")
        if path.name != "README.md"
    }
    core_agents = {
        path.name
        for path in (REPO_ROOT / "core" / "agents").glob("*.md")
        if path.name != "README.md"
    }

    assert live_agents
    assert live_agents <= core_agents


def test_core_templates_exist_for_live_templates():
    """Core should own canonical copies of reusable templates."""
    live_templates = {
        path.relative_to(REPO_ROOT / "templates")
        for path in (REPO_ROOT / "templates").rglob("*.template.md")
    }
    core_templates = {
        path.relative_to(REPO_ROOT / "core" / "templates")
        for path in (REPO_ROOT / "core" / "templates").rglob("*.template.md")
    }

    assert live_templates
    assert live_templates <= core_templates


def test_core_prompts_reference_core_templates():
    """Canonical prompts should not point to host-specific template installs."""
    for prompt_path in [
        REPO_ROOT / "core" / "prompts" / "plan.md",
        REPO_ROOT / "core" / "prompts" / "prd-import.md",
        REPO_ROOT / "core" / "prompts" / "bmad-import.md",
    ]:
        prompt = prompt_path.read_text(encoding="utf-8")

        assert "~/.claude/plugins" not in prompt
        assert "core/templates/plan/" in prompt


def test_codex_manifest_uses_natural_language_skill_prompts():
    """Codex examples should not promise plugin-defined slash commands."""
    manifest = json.loads((REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

    prompts = manifest["interface"]["defaultPrompt"]
    assert prompts
    assert all(prompt.startswith("Use Pathly") for prompt in prompts)
    assert all(not prompt.startswith("/") for prompt in prompts)


def test_codex_adapter_does_not_document_pathly_slash_command():
    """Current Codex builds expose Pathly as skills, not custom slash commands."""
    readme = (REPO_ROOT / "adapters" / "codex" / "README.md").read_text(encoding="utf-8")
    wrapper = (
        REPO_ROOT / "adapters" / "codex" / "skills" / "pathly" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "Use Pathly help" in readme
    assert "Do not document `/pathly` as a Codex command" in readme
    assert "Do not tell Codex users to type `/pathly ...`" in wrapper


def test_codex_manifest_has_no_placeholder_paths():
    """Published Codex metadata should not reference non-existent TODO resources."""
    manifest_text = (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    assert "[TODO:" not in manifest_text
    assert "hooks" not in manifest
    assert "mcpServers" not in manifest
    assert "apps" not in manifest


def test_pathly_router_namespaces_help_for_codex():
    """The Codex front door should prevent raw /help guidance from leaking back out."""
    router = (REPO_ROOT / "core" / "prompts" / "pathly.md").read_text(encoding="utf-8")

    assert "/help --doctor [feature]` -> `/pathly doctor [feature]" in router
    assert "/team-flow <feature> ...` -> `/pathly flow <feature> ..." in router
    assert "`verify-state` -> `core/prompts/verify-state.md`" in router
    assert "`prd-import` -> `core/prompts/prd-import.md`" in router


def test_path_alias_routes_like_pathly():
    """The short slash-command alias should exist and point users to the same router."""
    alias = (REPO_ROOT / "core" / "prompts" / "path.md").read_text(encoding="utf-8")

    assert "equivalent to `/pathly`" in alias
    assert "core/prompts/pathly.md" in alias
