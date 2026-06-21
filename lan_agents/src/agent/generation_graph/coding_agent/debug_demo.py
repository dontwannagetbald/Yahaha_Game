"""Local demo for Step-6 Coding Agent debug flow."""

from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path

from agent.generation_graph.asset_agent.run_asset_agent.node import run_asset_agent
from agent.generation_graph.coding_agent.debug_code_with_assets.node import (
    debug_code_with_assets,
)
from agent.generation_graph.orchestrator.planner import deterministic_contracts
from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.workspace import prepare_workspace, write_workspace_text
from agent.providers import MockLLMProvider, provider_from_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Step-6 Coding Debug demo")
    parser.add_argument(
        "--fixture",
        required=True,
        help="Path to the integrated bundle context fixture JSON",
    )
    parser.add_argument(
        "--workspace",
        default="output/debug-demo",
        help="Artifact workspace for generated assets and repaired bundle files",
    )
    args = parser.parse_args()

    raw_fixture = json.loads(Path(args.fixture).read_text())
    state = GenerationState(**raw_fixture["state"])
    state.artifact_workspace = str((Path.cwd() / args.workspace).resolve())

    if not state.development_brief or not state.asset_manifest_plan or not state.game_spec:
        contracts = deterministic_contracts(state)
        state.development_brief = contracts["development_brief"]
        state.asset_work_order = contracts["asset_work_order"]
        state.asset_manifest_plan = contracts["asset_manifest_plan"]
        state.game_spec = contracts["game_spec"]

    asset_update = run_asset_agent(state)
    state.processed_assets = asset_update["processed_assets"]
    state.asset_analysis = asset_update["asset_analysis"]

    _write_bundle_seed(state, raw_fixture["bundle_seed"])
    result = debug_code_with_assets(state, provider=_provider_for_demo(raw_fixture))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _write_bundle_seed(state: GenerationState, bundle_seed: dict) -> None:
    workspace = prepare_workspace(state.artifact_workspace)
    index_path = write_workspace_text(workspace, "index.html", bundle_seed["index_html"])
    style_path = write_workspace_text(workspace, "style.css", bundle_seed["style_css"])
    game_path = write_workspace_text(workspace, "game.js", bundle_seed["game_js"])
    manifest_path = write_workspace_text(
        workspace,
        "manifest_draft.json",
        json.dumps(bundle_seed["manifest_draft"], ensure_ascii=False, indent=2),
    )
    state.code_artifacts = {
        "index_html_path": str(index_path),
        "style_css_path": str(style_path),
        "game_js_path": str(game_path),
        "manifest_draft_path": str(manifest_path),
        "files": [
            {"relative_path": "index.html", "absolute_path": str(index_path)},
            {"relative_path": "style.css", "absolute_path": str(style_path)},
            {"relative_path": "game.js", "absolute_path": str(game_path)},
            {"relative_path": "manifest_draft.json", "absolute_path": str(manifest_path)},
        ],
        "referenced_asset_paths": list(bundle_seed.get("referenced_asset_paths", [])),
    }
    state.manifest_draft = bundle_seed["manifest_draft"]
    state.integrated_bundle_context = {
        "code_artifacts": deepcopy(state.code_artifacts),
        "manifest_draft": deepcopy(state.manifest_draft),
        "processed_assets": deepcopy(state.processed_assets),
        "asset_manifest_plan": deepcopy(state.asset_manifest_plan),
        "artifact_workspace": state.artifact_workspace,
    }


def _provider_for_demo(raw_fixture: dict):
    if os.environ.get("CODING_DEBUG_DEMO_USE_REAL_PROVIDER") == "1":
        return provider_from_env()

    repaired_manifest = deepcopy(raw_fixture["bundle_seed"]["manifest_draft"])
    repaired_manifest["assets"] = ["assets/background.png", "assets/player.png"]
    return MockLLMProvider(
        response={
            "game_js": "const canvas = document.getElementById('game'); const ctx = canvas.getContext('2d'); canvas.width = 960; canvas.height = 540; ctx.fillStyle = '#101418'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.fillStyle = '#ffc200'; ctx.font = '28px sans-serif'; ctx.fillText('Debug Demo Ready', 24, 40); window.parent.postMessage({ type: 'game_ready' }, '*');",
            "manifest_draft": repaired_manifest,
            "repair_notes": [
                "fixed syntax and restored game_ready signal",
                "kept manifest asset references aligned with bundle code",
            ],
        }
    )


if __name__ == "__main__":
    main()
