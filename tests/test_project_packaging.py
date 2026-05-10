"""Smoke tests for public plugin packaging and README commands."""

import json
import re
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_SKILL_ROOT = REPO_ROOT / "core" / "skills"
CLAUDE_AGENT_ROOT = REPO_ROOT / "adapters" / "claude" / "agents"
CLAUDE_PLUGIN_MANIFEST = (
    REPO_ROOT / "adapters" / "claude" / ".claude-plugin" / "plugin.json"
)
CLAUDE_MARKETPLACE = (
    REPO_ROOT / "adapters" / "claude" / ".claude-plugin" / "marketplace.json"
)
CODEX_MANIFEST_ROOT = REPO_ROOT / "adapters" / "codex"
CODEX_PLUGIN_MANIFEST = CODEX_MANIFEST_ROOT / ".codex-plugin" / "plugin.json"
CODEX_AGENT_ROOT = REPO_ROOT / "adapters" / "codex" / "agents"


def test_plugin_manifests_parse_and_point_to_skills():
    """Claude and Codex manifests should stay valid and point to core/skills."""
    for manifest_path in (CLAUDE_PLUGIN_MANIFEST, CODEX_PLUGIN_MANIFEST):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["name"] == "pathly"
        assert (REPO_ROOT / manifest["skills"]).resolve() == CORE_SKILL_ROOT.resolve()
        assert CORE_SKILL_ROOT.is_dir()

        if "agents" in manifest:
            agents_dir = (REPO_ROOT / manifest["agents"]).resolve()
            assert agents_dir.is_dir()


def test_public_marketplace_manifests_parse():
    """Published marketplace catalogs should expose Pathly from the repo root."""
    claude_marketplace = json.loads(CLAUDE_MARKETPLACE.read_text(encoding="utf-8"))
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
    ]
    assert "scripts*" not in pyproject["tool"]["setuptools"]["packages"]["find"]["include"]


def test_distribution_declares_runtime_assets_for_build_artifacts():
    """Built artifacts should carry core skills/templates and adapter agents."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    data_files = pyproject["tool"]["setuptools"]["data-files"]

    required_targets = {
        "pathly/core/skills": "core/skills/*.md",
        "pathly/core/agents": "core/agents/*.md",
        "pathly/core/templates/plan": "core/templates/plan/*.template.md",
        "pathly/adapters/codex/.codex-plugin": "adapters/codex/.codex-plugin/plugin.json",
        "pathly/adapters/codex/agents": "adapters/codex/agents/*.md",
        "pathly/adapters/claude/.claude-plugin": "adapters/claude/.claude-plugin/plugin.json",
        "pathly/adapters/claude/agents": "adapters/claude/agents/*.md",
    }

    for install_dir, source in required_targets.items():
        assert source in data_files[install_dir], f"Missing {source} in data-files[{install_dir}]"

    declared_sources = {
        source
        for sources in data_files.values()
        for source in sources
    }
    assert not any(source.startswith("scripts/") for source in declared_sources)
    assert not any(source.startswith("ho" + "oks/") for source in declared_sources)


def test_orchestrator_stays_top_level_runtime_package():
    """The Python FSM runtime should not be absorbed into core content files."""
    assert (REPO_ROOT / "orchestrator" / "__init__.py").exists()
    assert (REPO_ROOT / "orchestrator" / "reducer.py").exists()
    assert not (REPO_ROOT / "core" / "orchestrator").exists()


def test_claude_install_paths_use_pathly_plugin_dir():
    """Installers should install runtime plugin files under the Pathly name."""
    install_sh = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    install_ps1 = (REPO_ROOT / "install.ps1").read_text(encoding="utf-8")

    assert 'PLUGIN_NAME="pathly"' in install_sh
    assert '$PluginName = "pathly"' in install_ps1
    assert "pathly hooks install claude" in install_sh
    assert "pathly hooks install claude" in install_ps1
    assert "scripts/setup" + "-hook.sh" not in install_sh
    assert "scripts\\setup" + "-hook.ps1" not in install_ps1


def test_readme_slash_commands_map_to_skills():
    """Documented Pathly commands should not drift from the core skills."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    skill_names = {path.stem for path in CORE_SKILL_ROOT.glob("*.md")}

    # These slash-command entry points are the new-user front doors.
    documented_entrypoints = set(re.findall(r"/(pathly|path)(?=\s|$)", readme))
    assert {"pathly", "path"}.issubset(documented_entrypoints)
    assert documented_entrypoints <= skill_names

    # The README intentionally namespaces user-facing commands under /pathly.
    documented_pathly_commands = set(re.findall(r"/pathly\s+([a-z][a-z-]*)(?=\s|$)", readme))
    assert {"help", "doctor", "debug", "explore", "flow", "review"}.issubset(
        documented_pathly_commands
    )

    # The core skill table should only list real skills.
    documented_skill_rows = set(re.findall(r"^\| `([a-z][a-z-]*)` \| `/pathly", readme, re.MULTILINE))
    assert documented_skill_rows
    assert documented_skill_rows <= skill_names


def test_skills_are_canonical_core_files():
    """Skills should live directly in core/skills/ with no adapter wrappers."""
    skill_files = list(CORE_SKILL_ROOT.glob("*.md"))

    assert skill_files, "core/skills/ must contain skill files"
    for skill_file in skill_files:
        assert skill_file.is_file()
        assert skill_file.suffix == ".md"


def test_core_agent_contracts_exist_for_live_agents():
    """Core should own host-neutral copies of all adapter agent contracts."""
    core_agents = {
        path.name
        for path in (REPO_ROOT / "core" / "agents").glob("*.md")
        if path.name != "README.md"
    }

    for adapter in ("claude", "codex", "copilot"):
        agent_root = REPO_ROOT / "adapters" / adapter / "agents"
        if not agent_root.is_dir():
            continue
        live_agents = {
            path.name
            for path in agent_root.glob("*.md")
            if path.name != "README.md"
        }
        assert live_agents, f"adapters/{adapter}/agents/ has no agent files"
        assert live_agents <= core_agents, (
            f"adapters/{adapter}/agents/ has agents with no core contract: "
            f"{live_agents - core_agents}"
        )


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
    """Canonical skills should not point to host-specific template installs."""
    for skill_path in [
        REPO_ROOT / "core" / "skills" / "plan.md",
        REPO_ROOT / "core" / "skills" / "prd-import.md",
        REPO_ROOT / "core" / "skills" / "bmad-import.md",
    ]:
        prompt = skill_path.read_text(encoding="utf-8")

        assert "~/.claude/plugins" not in prompt
        assert "core/templates/plan/" in prompt


def test_codex_manifest_uses_natural_language_skill_prompts():
    """Codex examples should not promise plugin-defined slash commands."""
    manifest = json.loads(CODEX_PLUGIN_MANIFEST.read_text(encoding="utf-8"))

    prompts = manifest["interface"]["defaultPrompt"]
    assert prompts
    assert all(prompt.startswith("Use Pathly") for prompt in prompts)
    assert all(not prompt.startswith("/") for prompt in prompts)


def test_codex_adapter_does_not_document_pathly_slash_command():
    """Current Codex builds expose Pathly as skills, not custom slash commands."""
    readme = (REPO_ROOT / "adapters" / "codex" / "README.md").read_text(encoding="utf-8")

    assert "Use Pathly help" in readme
    assert "Do not document `/pathly` as a Codex command" in readme


def test_codex_agents_are_codex_safe():
    """Codex agent files should not use Claude-only model names or tools lists."""
    for agent_file in CODEX_AGENT_ROOT.glob("*.md"):
        if agent_file.name == "README.md":
            continue
        text = agent_file.read_text(encoding="utf-8")
        assert "model: haiku" not in text
        assert "model: sonnet" not in text
        assert "model: opus" not in text
        assert "tools: [" not in text


def test_core_help_menu_is_pathly_native_and_offers_storm():
    """The shared help workflow should not expose Claude branding as core behavior."""
    help_skill = (REPO_ROOT / "core" / "skills" / "help.md").read_text(encoding="utf-8")

    assert "Claude Agents Framework" not in help_skill
    assert "Brainstorm/refine an unclear idea" in help_skill
    assert "route to `storm <answer>`" in help_skill


def test_director_routes_to_workflow_ids_not_shell_commands():
    """The director should choose Pathly workflows; adapters render commands."""
    go_skill = (REPO_ROOT / "core" / "skills" / "go.md").read_text(encoding="utf-8")

    assert "Do not run a shell command merely because this prompt chooses a route" in go_skill
    assert "storm <topic>" in go_skill
    assert "team-flow <feature> lite" in go_skill
    assert "/pathly flow <feature> lite" not in go_skill


def test_codex_manifest_has_no_placeholder_paths():
    """Published Codex metadata should not reference non-existent TODO resources."""
    manifest_text = CODEX_PLUGIN_MANIFEST.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    assert "[TODO:" not in manifest_text
    assert "hooks" not in manifest
    assert "mcpServers" not in manifest
    assert "apps" not in manifest


def test_pathly_router_uses_host_neutral_routes():
    """The core front door should route by workflow id, not host command syntax."""
    router = (REPO_ROOT / "core" / "skills" / "pathly.md").read_text(encoding="utf-8")

    assert "This core router works in host-neutral route names" in router
    assert "host-specific command formatting" in router
    assert "`flow <feature>` instead of `team-flow <feature>`" in router
    assert "`verify-state` -> `core/skills/verify-state.md`" in router
    assert "`prd-import` -> `core/skills/prd-import.md`" in router


def test_path_alias_routes_like_pathly():
    """The short alias route should exist and point users to the same router."""
    alias = (REPO_ROOT / "core" / "skills" / "path.md").read_text(encoding="utf-8")

    assert "`path` is equivalent to `pathly`" in alias
    assert "core/skills/pathly.md" in alias


def test_core_prompts_do_not_leak_host_specific_surfaces():
    """Core skills should stay generic; adapters own host-specific invocation."""
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

    for skill_path in (REPO_ROOT / "core" / "skills").glob("*.md"):
        skill_text = skill_path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in skill_text, f"{skill_path.name} leaks {token}"


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
    """Meet should exist as a first-class skill in core/skills."""
    core_skill = REPO_ROOT / "core" / "skills" / "meet.md"
    assert core_skill.exists()


def test_pathly_router_and_help_reference_meet():
    """Meet should be reachable from the front door and visible in help."""
    router = (REPO_ROOT / "core" / "skills" / "pathly.md").read_text(encoding="utf-8")
    help_skill = (REPO_ROOT / "core" / "skills" / "help.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "### `meet`" in router
    assert "- `meet` -> `core/skills/meet.md`" in router
    assert "[5] Meet a role" in help_skill
    assert "route to `meet <feature>`" in help_skill
    assert "meet [feature]" in help_skill
    assert "| `meet` | `/pathly meet [feature]` |" in readme


# ---------------------------------------------------------------------------
# Phase 1 — Package resource contract (S1.1)
# ---------------------------------------------------------------------------

def test_resources_module_is_importable():
    """The host-neutral resource API must be importable as a top-level module."""
    import pathly.resources as resources
    assert callable(resources.core_prompt)
    assert callable(resources.core_agent)
    assert callable(resources.core_template)
    assert callable(resources.adapter_asset)
    assert callable(resources.list_core_prompts)
    assert callable(resources.list_core_agents)
    assert callable(resources.list_adapter_agents)
    assert callable(resources.copy_asset)
    assert callable(resources.copy_asset_tree)
    assert callable(resources.package_version)


def test_core_prompt_returns_existing_path():
    """core_prompt() must return a real file path for known prompts."""
    from pathly.resources import core_prompt

    path = core_prompt("help")
    assert path.exists()
    assert path.suffix == ".md"
    assert "help" in path.name


def test_core_prompt_raises_for_missing_prompt():
    """core_prompt() must raise FileNotFoundError for non-existent prompts."""
    from pathly.resources import core_prompt
    import pytest

    with pytest.raises(FileNotFoundError, match="core/skills"):
        core_prompt("_does_not_exist_xyz")


def test_core_agent_returns_existing_path():
    """core_agent() must return a real file path for known agent contracts."""
    from pathly.resources import core_agent

    path = core_agent("builder.md")
    assert path.exists()
    assert path.name == "builder.md"


def test_core_agent_raises_for_missing_agent():
    """core_agent() must raise FileNotFoundError for non-existent agents."""
    from pathly.resources import core_agent
    import pytest

    with pytest.raises(FileNotFoundError, match="core/agents"):
        core_agent("_no_such_agent.md")


def test_core_template_returns_existing_path():
    """core_template() must return a real template file."""
    from pathly.resources import list_core_prompts, _asset_root
    from pathly import resources

    root = _asset_root()
    template_dir = root / "core" / "templates" / "plan"
    templates = list(template_dir.glob("*.template.md"))
    assert templates, "Expected at least one core template"

    first = templates[0]
    path = resources.core_template(first.name)
    assert path.exists()
    assert path.name == first.name


def test_core_template_raises_for_missing_template():
    """core_template() must raise FileNotFoundError for non-existent templates."""
    from pathly.resources import core_template
    import pytest

    with pytest.raises(FileNotFoundError, match="core/templates"):
        core_template("_no_such_template.template.md")


def test_adapter_asset_returns_existing_path():
    """adapter_asset() must resolve adapter files from packaged resources."""
    from pathly.resources import adapter_asset

    path = adapter_asset("claude", "README.md")
    assert path.exists()


def test_adapter_asset_raises_for_missing_asset():
    """adapter_asset() must raise FileNotFoundError for non-existent adapter files."""
    from pathly.resources import adapter_asset
    import pytest

    with pytest.raises(FileNotFoundError, match="adapters"):
        adapter_asset("claude", "_no_such_file.md")


def test_list_core_prompts_returns_all_prompts():
    """list_core_prompts() must return a non-empty list of .md files."""
    from pathly.resources import list_core_prompts

    prompts = list_core_prompts()
    assert prompts
    assert all(p.suffix == ".md" for p in prompts)
    names = {p.name for p in prompts}
    assert "help.md" in names
    assert "go.md" in names


def test_list_core_agents_excludes_readme():
    """list_core_agents() must exclude README.md from results."""
    from pathly.resources import list_core_agents

    agents = list_core_agents()
    assert agents
    names = {p.name for p in agents}
    assert "README.md" not in names
    assert "builder.md" in names


def test_list_adapter_agents_returns_agent_files():
    """list_adapter_agents() must return agent file paths for a known adapter."""
    from pathly.resources import list_adapter_agents

    agents = list_adapter_agents("claude")
    assert agents
    assert all(p.is_file() for p in agents)
    names = {p.name for p in agents}
    assert "builder.md" in names
    assert "reviewer.md" in names


def test_copy_asset_copies_file_to_destination(tmp_path):
    """copy_asset() must copy a packaged file to a destination path."""
    from pathly.resources import core_prompt, copy_asset

    src = core_prompt("help")
    dest = tmp_path / "prompts" / "help.md"

    copy_asset(src, dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_copy_asset_tree_copies_directory(tmp_path):
    """copy_asset_tree() must recursively copy a packaged directory."""
    from pathly.resources import copy_asset_tree, _asset_root

    root = _asset_root()
    src_dir = root / "core" / "skills"
    dest_dir = tmp_path / "prompts"

    copy_asset_tree(src_dir, dest_dir)

    assert dest_dir.is_dir()
    assert (dest_dir / "help.md").exists()


def test_package_version_returns_version_string():
    """package_version() must return a non-empty version string."""
    from pathly.resources import package_version

    version = package_version()
    assert version
    assert version != "unknown"
    assert "." in version


# ---------------------------------------------------------------------------
# Phase 2 — Clean install smoke (S1.2)
# ---------------------------------------------------------------------------

def test_pathly_version_flag_prints_version():
    """pathly --version must print the version without a subcommand."""
    import subprocess, sys

    result = subprocess.run(
        [sys.executable, "-m", "pathly.cli", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.startswith("pathly ")
    assert "." in result.stdout


def test_pathly_help_runs_from_non_pathly_directory(tmp_path):
    """pathly --help must succeed from a directory that is not the Pathly source tree."""
    import subprocess, sys

    result = subprocess.run(
        [sys.executable, "-m", "pathly.cli", "--help"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Pathly" in result.stdout


def test_pathly_doctor_runs_from_non_pathly_directory(tmp_path):
    """pathly doctor must not crash when run from a non-Pathly directory."""
    import subprocess, sys

    result = subprocess.run(
        [sys.executable, "-m", "pathly.cli", "--project-dir", str(tmp_path), "doctor"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert result.returncode in {0, 1}
    assert "Project:" in result.stdout
