from __future__ import annotations

from pathlib import Path

from app.tools.bundle_tools import write_bundle
from app.tools.manifest_tools import build_manifest


def generate_bundle(game_spec: dict[str, object], output_dir: Path) -> dict[str, object]:
    manifest = build_manifest(
        title=str(game_spec["title"]),
        description=str(game_spec["description"]),
    )
    files = write_bundle(
        output_dir=output_dir,
        title=str(game_spec["title"]),
        description=str(game_spec["description"]),
        manifest=manifest,
    )
    return {
        "artifact_prefix": str(output_dir),
        "manifest_path": str(output_dir / "manifest.json"),
        "entry_path": str(output_dir / "index.html"),
        "files": files,
    }

