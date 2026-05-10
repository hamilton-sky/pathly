from importlib.resources import files
from pathlib import Path


def _root() -> Path:
    # Works for editable installs; install_cli/ sits alongside core/ and adapters/
    return Path(str(files("install_cli"))).parent


def core_agents_path() -> Path:
    return _root() / "core" / "agents"


def core_skills_path() -> Path:
    return _root() / "core" / "skills"


def adapters_path() -> Path:
    return _root() / "adapters"


def adapter_meta_path(host: str) -> Path:
    return adapters_path() / host / "_meta"


def adapter_install_yaml(host: str) -> Path:
    return adapter_meta_path(host) / "install.yaml"
