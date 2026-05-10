import json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = ".pathly-manifest.json"


def _load_manifest(dest: Path) -> dict:
    manifest_path = dest / MANIFEST_NAME
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"files": {}}
    return {"files": {}}


def _save_manifest(dest: Path, manifest: dict) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def materialize(
    files: dict[str, str],
    dest: Path,
    *,
    repair: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> list[str]:
    """Copy stitched agent files to dest. Returns list of filenames written (or would-write)."""
    manifest = _load_manifest(dest)
    owned = set(manifest["files"].keys())
    written: list[str] = []

    for name, content in files.items():
        target = dest / name
        if target.exists():
            if name in owned and not repair:
                continue
            if name not in owned and not force:
                continue

        written.append(name)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            manifest["files"][name] = datetime.now(timezone.utc).isoformat()

    if not dry_run and written:
        _save_manifest(dest, manifest)

    return written
