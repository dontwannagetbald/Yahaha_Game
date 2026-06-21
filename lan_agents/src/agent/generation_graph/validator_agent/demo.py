"""Local demo for Step-7 Validator Agent final delivery checks."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from agent.generation_graph.asset_agent.tools.image_processing import (
    write_chroma_keyed_player,
    write_mock_background,
    write_mock_cover,
)
from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.workspace import prepare_workspace, write_workspace_text
from agent.generation_graph.validator_agent.validate_final_delivery.node import (
    validate_final_delivery,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Step-7 Validator demo")
    parser.add_argument(
        "--fixture",
        required=True,
        help="Path to the validated bundle context fixture JSON",
    )
    parser.add_argument(
        "--workspace",
        default="output/validator-demo",
        help="Artifact workspace for the bundle under validation",
    )
    args = parser.parse_args()

    raw_fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    state = GenerationState(**raw_fixture["state"])
    state.artifact_workspace = str((Path.cwd() / args.workspace).resolve())

    _write_assets(state)
    _write_bundle(state, raw_fixture["bundle_seed"])
    result = validate_final_delivery(state)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _write_assets(state: GenerationState) -> None:
    workspace = Path(state.artifact_workspace)
    background_path = workspace / "assets" / "background.png"
    player_path = workspace / "assets" / "player.png"
    cover_path = workspace / "assets" / "cover.png"
    write_mock_background(background_path)
    write_chroma_keyed_player(player_path)
    write_mock_cover(cover_path)
    state.processed_assets = [
        {
            "target_path": "assets/background.png",
            "path": str(background_path),
            "runtime_required": True,
        },
        {
            "target_path": "assets/player.png",
            "path": str(player_path),
            "runtime_required": True,
        },
        {
            "target_path": "assets/cover.png",
            "path": str(cover_path),
            "runtime_required": False,
        },
    ]


def _write_bundle(state: GenerationState, bundle_seed: dict) -> None:
    workspace = prepare_workspace(state.artifact_workspace)
    manifest = bundle_seed["manifest"]
    index_path = write_workspace_text(workspace, "index.html", bundle_seed["index_html"])
    style_path = write_workspace_text(workspace, "style.css", bundle_seed["style_css"])
    game_path = write_workspace_text(workspace, "game.js", bundle_seed["game_js"])
    manifest_path = write_workspace_text(
        workspace,
        "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )
    state.manifest_draft = manifest
    state.code_artifacts = {
        "index_html_path": str(index_path),
        "style_css_path": str(style_path),
        "game_js_path": str(game_path),
        "manifest_path": str(manifest_path),
        "files": [
            {"relative_path": "index.html", "absolute_path": str(index_path)},
            {"relative_path": "style.css", "absolute_path": str(style_path)},
            {"relative_path": "game.js", "absolute_path": str(game_path)},
            {"relative_path": "manifest.json", "absolute_path": str(manifest_path)},
        ],
        "referenced_asset_paths": list(bundle_seed.get("referenced_asset_paths", [])),
    }
    state.integrated_bundle_context = {
        "code_artifacts": deepcopy(state.code_artifacts),
        "manifest_draft": deepcopy(state.manifest_draft),
        "processed_assets": deepcopy(state.processed_assets),
        "asset_manifest_plan": deepcopy(state.asset_manifest_plan),
        "artifact_workspace": state.artifact_workspace,
    }


if __name__ == "__main__":
    main()
