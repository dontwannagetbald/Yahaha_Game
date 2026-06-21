"""Local demo for stage-B Asset Agent asset generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent.generation_graph.asset_agent.run_asset_agent.node import run_asset_agent
from agent.generation_graph.orchestrator.planner import deterministic_contracts
from agent.generation_graph.state import GenerationState

MVP_ASSET_PATHS = {
    "assets/background.png",
    "assets/player.png",
    "assets/cover.png",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the stage-B Asset Agent demo")
    parser.add_argument("--fixture", required=True, help="Path to generation fixture JSON")
    parser.add_argument(
        "--workspace",
        default="output/asset-demo",
        help="Artifact workspace for generated assets",
    )
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text())
    state = GenerationState(**fixture)
    contracts = deterministic_contracts(state)
    manifest_paths = {item.get("target_path") for item in state.asset_manifest_plan}
    if not MVP_ASSET_PATHS.issubset(manifest_paths):
        state.development_brief = contracts["development_brief"]
        state.asset_work_order = contracts["asset_work_order"]
        state.asset_manifest_plan = contracts["asset_manifest_plan"]
        state.game_spec = contracts["game_spec"]
    else:
        state.development_brief = state.development_brief or contracts["development_brief"]
        state.asset_work_order = state.asset_work_order or contracts["asset_work_order"]
        state.game_spec = state.game_spec or contracts["game_spec"]
    state.artifact_workspace = args.workspace

    result = run_asset_agent(state)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
