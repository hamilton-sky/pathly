"""Static alignment checks — docs and pyproject.toml match verified behavior."""
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent

ROOT_README = REPO_ROOT / "README.md"
ADAPTERS_README = REPO_ROOT / "pathly-adapters" / "README.md"
ENGINE_README = REPO_ROOT / "pathly-engine" / "README.md"
ADAPTERS_PYPROJECT = REPO_ROOT / "pathly-adapters" / "pyproject.toml"
ENGINE_PYPROJECT = REPO_ROOT / "pathly-engine" / "pyproject.toml"


# --- README files exist ---

def test_root_readme_exists():
    assert ROOT_README.exists()


def test_adapters_readme_exists():
    assert ADAPTERS_README.exists()


def test_engine_readme_exists():
    assert ENGINE_README.exists()


def test_claude_adapter_readme_exists():
    assert (REPO_ROOT / "pathly-adapters" / "adapters" / "claude" / "README.md").exists()


def test_codex_adapter_readme_exists():
    assert (REPO_ROOT / "pathly-adapters" / "adapters" / "codex" / "README.md").exists()


def test_copilot_adapter_readme_exists():
    assert (REPO_ROOT / "pathly-adapters" / "adapters" / "copilot" / "README.md").exists()


# --- pyproject.toml entry points ---

def test_adapters_pyproject_entry_point():
    text = ADAPTERS_PYPROJECT.read_text(encoding="utf-8")
    assert "pathly-setup" in text, "pathly-adapters/pyproject.toml must declare pathly-setup entry point"


def test_engine_pyproject_entry_point():
    text = ENGINE_PYPROJECT.read_text(encoding="utf-8")
    assert re.search(r"pathly\s*=", text), "pathly-engine/pyproject.toml must declare pathly entry point"


# --- Root README mentions both sub-project installs ---

def test_root_readme_mentions_adapters_install():
    text = ROOT_README.read_text(encoding="utf-8")
    assert "pathly-adapters" in text, "Root README must mention pathly-adapters"


def test_root_readme_mentions_engine_install():
    text = ROOT_README.read_text(encoding="utf-8")
    assert "pathly-engine" in text, "Root README must mention pathly-engine"


def test_root_readme_no_old_monolith_install():
    text = ROOT_README.read_text(encoding="utf-8")
    assert 'pip install -e ".[dev]"' not in text, "Root README must not reference old monolith install"
    assert "pathly install codex" not in text, "Root README must not reference old 'pathly install codex' command"
    assert "pathly install claude" not in text, "Root README must not reference old 'pathly install claude' command"


# --- pathly-adapters README documents pathly-setup ---

def test_adapters_readme_documents_pathly_setup():
    text = ADAPTERS_README.read_text(encoding="utf-8")
    assert "pathly-setup" in text, "pathly-adapters/README.md must document pathly-setup"
    assert "--dry-run" in text, "pathly-adapters/README.md must document --dry-run flag"
    assert "--apply" in text, "pathly-adapters/README.md must document --apply flag"


# --- pathly-engine README documents engine CLI ---

def test_engine_readme_documents_go():
    text = ENGINE_README.read_text(encoding="utf-8")
    assert "pathly go" in text, "pathly-engine/README.md must document 'pathly go'"


def test_engine_readme_documents_status():
    text = ENGINE_README.read_text(encoding="utf-8")
    assert "pathly status" in text, "pathly-engine/README.md must document 'pathly status'"


def test_engine_readme_documents_doctor():
    text = ENGINE_README.read_text(encoding="utf-8")
    assert "pathly doctor" in text, "pathly-engine/README.md must document 'pathly doctor'"


# --- Claude Code and Codex examples are kept separate ---

def test_root_readme_claude_uses_slash_commands():
    text = ROOT_README.read_text(encoding="utf-8")
    assert "/pathly" in text, "Root README must show Claude Code slash-command examples"


def test_root_readme_codex_uses_natural_language():
    text = ROOT_README.read_text(encoding="utf-8")
    assert "Use Pathly" in text, "Root README must show Codex natural-language examples"
