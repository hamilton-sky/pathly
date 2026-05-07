"""Smoke tests for public plugin packaging and README commands."""

import json
import re
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SKILL_ROOT = REPO_ROOT / "adapters" / "claude-code" / "skills"
CLAUDE_AGENT_ROOT = REPO_ROOT / "adapters" / "claude-code" / "agents"
CODEX_SKILL_ROOT = REPO_ROOT / "adapters" / "codex" / "skills"
AGENTS_SKILL_ROOT = REPO_ROOT / ".agents" / "skills"


def test_plugin_manifests_parse_and_point_to_skills():
    """Claude and Codex manifests should stay valid as branding changes."""
    expected_skill_dirs = {
        REPO_ROOT / ".claude-plugin" / "plugin.json": (REPO_ROOT, CLAUDE_SKILL_ROOT),
        REPO_ROOT / ".codex-plugin" / "plugin.json": (REPO_ROOT, CODEX_SKILL_ROOT),
        REPO_ROOT / "adapters" / "codex" / ".codex-plugin" / "plugin.json": (
            REPO_ROOT / "adapters" / "codex",
            CODEX_SKILL_ROOT,
        ),
    }

    for manifest_path, (manifest_root, expected_skill_dir) in expected_skill_dirs.items():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["name"] == "pathly"
        assert manifest["version"]
        assert (manifest_root / manifest["skills"]).resolve() == expected_skill_dir.resolve()
        assert expected_skill_dir.is_dir()

        if "agents" in manifest:
            assert (manifest_root / manifest["agents"]).resolve() == CLAUDE_AGENT_ROOT.resolve()
            assert CLAUDE_AGENT_ROOT.is_dir()


def test_public_marketplace_manifests_parse():
    """Published marketplace catalogs should expose Pathly from the repo root."""
    claude_marketplace = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    codex_marketplace = json.loads(
        (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )

    assert claude_marketplace["name"] == "pathly"
    assert claude_marketplace["owner"]["name"] == "hamilton"
    assert claude_marketplace["plugins"][0]["name"] == "pathly"
    assert claude_marketplace["plugins"][0]["source"] == "./"
    assert claude_marketplace["plugins"][0]["version"] == "2.0.0"

    assert codex_marketplace["name"] == "pathly"
    assert codex_marketplace["interface"]["displayName"] == "Pathly"
    assert codex_marketplace["plugins"][0]["name"] == "pathly"
    assert codex_marketplace["plugins"][0]["source"] == {
        "source": "local",
        "path": "./",
    }
    assert codex_marketplace["plugins"][0]["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }


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
    assert "classify_feedback.py" in setup_hook_sh
    assert "inject_feedback_ttl.py" in setup_hook_sh
    assert "classify_feedback.py" in setup_hook_ps1
    assert "inject_feedback_ttl.py" in setup_hook_ps1


def test_readme_slash_commands_map_to_skills():
    """Documented Pathly commands should not drift from the skill folders."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    skill_names = {path.name for path in CLAUDE_SKILL_ROOT.iterdir() if path.is_dir()}

    # These slash-command entry points are the new-user front doors.
    documented_entrypoints = set(re.findall(r"/(pathly|path)(?=\s|$)", readme))
    assert {"pathly", "path"}.issubset(documented_entrypoints)
    assert documented_entrypoints <= skill_names

    # The README intentionally namespaces user-facing commands under /pathly.
    documented_pathly_commands = set(re.findall(r"/pathly\s+([a-z][a-z-]*)(?=\s|$)", readme))
    assert {"help", "doctor", "debug", "explore", "flow", "review"}.issubset(
        documented_pathly_commands
    )

    # The core skill table should only list real Claude adapter skills.
    documented_skill_rows = set(re.findall(r"^\| `([a-z][a-z-]*)` \| `/pathly", readme, re.MULTILINE))
    assert documented_skill_rows
    assert documented_skill_rows <= skill_names


def test_skills_are_core_backed_wrappers():
    """Live slash-command skills should point at canonical core prompts."""
    skill_dirs = [path for path in CLAUDE_SKILL_ROOT.iterdir() if path.is_dir()]

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
        for path in CLAUDE_AGENT_ROOT.glob("*.md")
        if path.name != "README.md"
    }
    core_agents = {
        path.name
        for path in (REPO_ROOT / "core" / "agents").glob("*.md")
        if path.name != "README.md"
    }

    assert live_agents
    assert live_agents <= core_agents


def test_core_templates_are_canonical():
    """Reusable templates should live only under core/templates."""
    template_root = REPO_ROOT / "core" / "templates"
    core_templates = {
        path.relative_to(REPO_ROOT / "core" / "templates")
        for path in template_root.rglob("*.template.md")
    }

    assert core_templates
    assert not (REPO_ROOT / "templates").exists()


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


def test_codex_adapter_skills_are_codex_safe_core_wrappers():
    """Codex wrappers should use core prompts without Claude-only model labels."""
    manifest = json.loads((REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    codex_skill_root = (REPO_ROOT / manifest["skills"]).resolve()
    claude_skill_names = {path.name for path in CLAUDE_SKILL_ROOT.iterdir() if path.is_dir()}
    codex_skill_names = {path.name for path in codex_skill_root.iterdir() if path.is_dir()}

    assert claude_skill_names <= codex_skill_names

    for skill_dir in codex_skill_root.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        core_prompt = REPO_ROOT / "core" / "prompts" / f"{skill_dir.name}.md"

        assert core_prompt.exists(), f"Missing core prompt for {skill_dir.name}"
        assert f"core/prompts/{skill_dir.name}.md" in skill_text
        assert "model: haiku" not in skill_text
        assert "model: sonnet" not in skill_text
        assert "model: opus" not in skill_text


def test_agents_skills_mirror_codex_safe_wrappers():
    """Direct agent skill discovery should expose the same Codex-safe wrappers."""
    assert AGENTS_SKILL_ROOT.is_dir()

    codex_skill_names = {path.name for path in CODEX_SKILL_ROOT.iterdir() if path.is_dir()}
    agents_skill_names = {path.name for path in AGENTS_SKILL_ROOT.iterdir() if path.is_dir()}

    assert agents_skill_names == codex_skill_names

    for skill_name in codex_skill_names:
        codex_skill = CODEX_SKILL_ROOT / skill_name / "SKILL.md"
        agents_skill = AGENTS_SKILL_ROOT / skill_name / "SKILL.md"

        assert agents_skill.exists()
        assert agents_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")


def test_codex_skills_match_adapter_wrapper_shape():
    """Codex skills should mirror Claude wrapper structure with Codex invocation rules."""
    for skill_dir in CODEX_SKILL_ROOT.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_name = skill_dir.name
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

        assert f"# you are at adapters/codex/skills/{skill_name}/SKILL.md." in skill_text
        assert "0. User invokes this skill with natural language" in skill_text
        assert f"Read `core/prompts/{skill_name}.md`" in skill_text
        assert "plugin-defined slash commands" in skill_text
        assert "CLI fallback" in skill_text
        assert f"pathly/core/prompts/{skill_name}.md" not in skill_text


def test_codex_director_and_team_flow_do_not_fall_back_to_cli():
    """Codex workflow skills should route in-plugin unless CLI fallback is explicit."""
    for skill_name in ["go", "help", "pathly", "team-flow"]:
        skill_text = (
            REPO_ROOT / "adapters" / "codex" / "skills" / skill_name / "SKILL.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(skill_text.split())

        assert "CLI fallback" in skill_text
        assert "unless the user explicitly asks" in normalized


def test_codex_help_requires_core_numbered_menu():
    """Pathly help should not collapse into the terse CLI help output."""
    help_skill = (CODEX_SKILL_ROOT / "help" / "SKILL.md").read_text(encoding="utf-8")
    pathly_skill = (CODEX_SKILL_ROOT / "pathly" / "SKILL.md").read_text(encoding="utf-8")

    assert "numbered interactive menu" in help_skill
    assert "See all commands" in help_skill
    assert "Plans:" in help_skill
    assert "Next:" in help_skill
    assert "numbered menu from `core/prompts/help.md`" in pathly_skill


def test_core_help_menu_is_pathly_native_and_offers_storm():
    """The shared help workflow should not expose Claude branding as core behavior."""
    help_prompt = (REPO_ROOT / "core" / "prompts" / "help.md").read_text(encoding="utf-8")

    assert "Claude Agents Framework" not in help_prompt
    assert "Brainstorm/refine an unclear idea" in help_prompt
    assert "route to `storm <answer>`" in help_prompt


def test_director_routes_to_workflow_ids_not_shell_commands():
    """The director should choose Pathly workflows; adapters render commands."""
    go_prompt = (REPO_ROOT / "core" / "prompts" / "go.md").read_text(encoding="utf-8")

    assert "Do not run a shell command merely because this prompt chooses a route" in go_prompt
    assert "storm <topic>" in go_prompt
    assert "team-flow <feature> lite" in go_prompt
    assert "/pathly flow <feature> lite" not in go_prompt


def test_codex_manifest_has_no_placeholder_paths():
    """Published Codex metadata should not reference non-existent TODO resources."""
    manifest_text = (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    assert "[TODO:" not in manifest_text
    assert "hooks" not in manifest
    assert "mcpServers" not in manifest
    assert "apps" not in manifest


def test_pathly_router_uses_host_neutral_routes():
    """The core front door should route by workflow id, not host command syntax."""
    router = (REPO_ROOT / "core" / "prompts" / "pathly.md").read_text(encoding="utf-8")

    assert "This core router works in host-neutral route names" in router
    assert "host-specific command formatting" in router
    assert "`flow <feature>` instead of `team-flow <feature>`" in router
    assert "`verify-state` -> `core/prompts/verify-state.md`" in router
    assert "`prd-import` -> `core/prompts/prd-import.md`" in router


def test_path_alias_routes_like_pathly():
    """The short alias route should exist and point users to the same router."""
    alias = (REPO_ROOT / "core" / "prompts" / "path.md").read_text(encoding="utf-8")

    assert "`path` is equivalent to `pathly`" in alias
    assert "core/prompts/pathly.md" in alias


def test_core_prompts_do_not_leak_host_specific_surfaces():
    """Core prompts should stay generic; adapters own host-specific invocation."""
    forbidden = [
        "`/pathly",
        " /pathly",
        "~/.claude",
        ".claude",
        "CLAUDE.md",
        "Claude Code",
        "Codex",
        "model=\"haiku\"",
        "model: haiku",
        "model: sonnet",
        "model: opus",
    ]

    for prompt_path in (REPO_ROOT / "core" / "prompts").glob("*.md"):
        prompt_text = prompt_path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in prompt_text, f"{prompt_path.name} leaks {token}"


def test_readme_discloses_beta_limitations():
    """Public README should not imply Pathly is production-ready before release gates."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "public beta candidate" in readme
    assert "not a production-ready release" in readme
    assert "Known limitations today" in readme
    assert "End-to-end agent behavior" in readme


def test_production_readiness_matches_current_cli_contract():
    """Production readiness docs should not drift from the shipped pathly CLI."""
    readiness = (REPO_ROOT / "docs" / "PRODUCTION_READINESS.md").read_text(encoding="utf-8")
    parser = __import__("pathly.cli", fromlist=["build_parser"]).build_parser()
    commands = set(parser._subparsers._group_actions[0].choices)

    assert "Not yet a standalone Python CLI" not in readiness
    assert "Packaged as a Python CLI named `pathly`" in readiness
    assert {"install", "init", "help", "doctor", "debug", "explore", "review", "flow"} <= commands
    for command in ["install", "init", "help", "doctor", "debug", "explore", "review", "flow"]:
        assert f"pathly {command}" in readiness

def test_meet_skill_is_packaged_and_core_backed():
    """Meet should exist as a first-class skill across adapters and core prompts."""
    core_prompt = REPO_ROOT / "core" / "prompts" / "meet.md"
    claude_skill = REPO_ROOT / "adapters" / "claude-code" / "skills" / "meet" / "SKILL.md"
    codex_skill = REPO_ROOT / "adapters" / "codex" / "skills" / "meet" / "SKILL.md"
    agents_skill = REPO_ROOT / ".agents" / "skills" / "meet" / "SKILL.md"

    assert core_prompt.exists()
    assert claude_skill.exists()
    assert codex_skill.exists()
    assert agents_skill.exists()
    assert "core/prompts/meet.md" in claude_skill.read_text(encoding="utf-8")
    assert "core/prompts/meet.md" in codex_skill.read_text(encoding="utf-8")
    assert agents_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")


def test_pathly_router_and_help_reference_meet():
    """Meet should be reachable from the front door and visible in help."""
    router = (REPO_ROOT / "core" / "prompts" / "pathly.md").read_text(encoding="utf-8")
    help_prompt = (REPO_ROOT / "core" / "prompts" / "help.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "### `meet`" in router
    assert "- `meet` -> `core/prompts/meet.md`" in router
    assert "[5] Meet a role" in help_prompt
    assert "route to `meet <feature>`" in help_prompt
    assert "meet [feature]" in help_prompt
    assert "| `meet` | `/pathly meet [feature]` |" in readme
