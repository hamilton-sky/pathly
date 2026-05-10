"""Tests for the two-project split structure."""
import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent


def test_adapters_pyproject_exists():
    assert (REPO_ROOT / "pathly-adapters" / "pyproject.toml").exists()


def test_engine_pyproject_exists():
    assert (REPO_ROOT / "pathly-engine" / "pyproject.toml").exists()


def test_adapters_install_cli_init_exists():
    assert (REPO_ROOT / "pathly-adapters" / "install_cli" / "__init__.py").exists()


def test_engine_cli_init_exists():
    assert (REPO_ROOT / "pathly-engine" / "engine_cli" / "__init__.py").exists()


def test_adapters_core_dir_exists():
    assert (REPO_ROOT / "pathly-adapters" / "core").is_dir()


def test_adapters_adapters_dir_exists():
    assert (REPO_ROOT / "pathly-adapters" / "adapters").is_dir()


def test_engine_orchestrator_dir_exists():
    assert (REPO_ROOT / "pathly-engine" / "orchestrator").is_dir()


def test_engine_runners_dir_exists():
    assert (REPO_ROOT / "pathly-engine" / "runners").is_dir()


def test_engine_team_flow_dir_exists():
    assert (REPO_ROOT / "pathly-engine" / "team_flow").is_dir()


def _get_top_level_imports(path: pathlib.Path) -> list[str]:
    """Return top-level module names imported in a Python file."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imports.append(node.module.split(".")[0])
    return imports


def test_engine_no_cross_imports_to_adapters():
    """No .py file under pathly-engine/ should import from pathly-adapters or install_cli."""
    forbidden = {"pathly_adapters", "install_cli"}
    engine_dir = REPO_ROOT / "pathly-engine"
    violations = []
    for py_file in engine_dir.rglob("*.py"):
        for mod in _get_top_level_imports(py_file):
            if mod in forbidden:
                violations.append(f"{py_file}: imports '{mod}'")
    assert not violations, "Cross-import violations found:\n" + "\n".join(violations)


def test_adapters_no_cross_imports_to_engine():
    """No .py file under pathly-adapters/install_cli/ should import from engine packages."""
    forbidden = {"pathly_engine", "orchestrator", "runners", "team_flow"}
    install_cli_dir = REPO_ROOT / "pathly-adapters" / "install_cli"
    violations = []
    for py_file in install_cli_dir.rglob("*.py"):
        for mod in _get_top_level_imports(py_file):
            if mod in forbidden:
                violations.append(f"{py_file}: imports '{mod}'")
    assert not violations, "Cross-import violations found:\n" + "\n".join(violations)
