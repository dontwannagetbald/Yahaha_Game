"""Local demo runner for the second-stage generation graph."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from agent.generation_graph.graph import generation_graph


def run_generation_demo(
    *,
    fixture: dict[str, Any],
    workspace: str,
    no_visual_assets: bool = False,
    use_real_provider: bool = False,
) -> dict[str, Any]:
    """Run the generation graph and return printable debug output."""
    state = dict(fixture)
    if no_visual_assets:
        state["uploaded_assets"] = []
        state["material_usage"] = {"assets": []}
    state["artifact_workspace"] = workspace

    previous_provider = os.environ.get("LLM_PROVIDER")
    previous_asset_provider = os.environ.get("ASSET_IMAGE_PROVIDER")
    if not use_real_provider:
        os.environ["LLM_PROVIDER"] = "mock"
        os.environ["ASSET_IMAGE_PROVIDER"] = "mock"
    try:
        final_state = generation_graph.invoke(state)
    finally:
        if not use_real_provider:
            if previous_provider is None:
                os.environ.pop("LLM_PROVIDER", None)
            else:
                os.environ["LLM_PROVIDER"] = previous_provider
            if previous_asset_provider is None:
                os.environ.pop("ASSET_IMAGE_PROVIDER", None)
            else:
                os.environ["ASSET_IMAGE_PROVIDER"] = previous_asset_provider
    output = _format_generation_output(final_state, workspace)
    return {
        "workspace": workspace,
        "final_state": final_state,
        "output": output,
    }


def _format_generation_output(state: dict[str, Any], workspace: str) -> str:
    sections = [
        "[Workspace]",
        workspace,
        "[Orchestrator Asset Decisions]",
        json.dumps(
            state.get("asset_work_order", {}).get("asset_decisions", []),
            ensure_ascii=False,
            indent=2,
        ),
        "[Coding Agent Brief]",
        json.dumps(state.get("coding_agent_brief", {}), ensure_ascii=False, indent=2),
        "[Asset Agent Brief]",
        json.dumps(state.get("asset_agent_brief", {}), ensure_ascii=False, indent=2),
        "[Asset Manifest Plan]",
        json.dumps(state.get("asset_manifest_plan", []), ensure_ascii=False, indent=2),
        "[Processed Assets]",
        json.dumps(state.get("processed_assets", []), ensure_ascii=False, indent=2),
        "[Generated Files]",
        json.dumps(_generated_files(state), ensure_ascii=False, indent=2),
        "[Manifest Draft]",
        json.dumps(state.get("manifest_draft", {}), ensure_ascii=False, indent=2),
        "[Debug Report]",
        json.dumps(state.get("debug_report", {}), ensure_ascii=False, indent=2),
        "[Validation Report]",
        json.dumps(state.get("validation_report", {}), ensure_ascii=False, indent=2),
        "[Artifact Result]",
        json.dumps(state.get("artifact_result", {}), ensure_ascii=False, indent=2),
    ]
    return "\n".join(sections)


def _generated_files(state: dict[str, Any]) -> list[dict[str, str]]:
    files = []
    for item in state.get("code_artifacts", {}).get("files", []):
        if isinstance(item, dict):
            files.append(
                {
                    "relative_path": str(item.get("relative_path", "")),
                    "absolute_path": str(item.get("absolute_path", "")),
                }
            )
    for item in state.get("processed_assets", []):
        if isinstance(item, dict):
            files.append(
                {
                    "relative_path": str(item.get("target_path", "")),
                    "absolute_path": str(item.get("path", "")),
                }
            )
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full generation graph demo.")
    parser.add_argument("--fixture", required=True, help="Path to confirmed session fixture")
    parser.add_argument(
        "--workspace",
        default="output/generation-demo",
        help="Artifact workspace for generated bundle files",
    )
    parser.add_argument(
        "--no-visual-assets",
        action="store_true",
        help="Clear uploaded visual assets to test the code-generated branch.",
    )
    parser.add_argument(
        "--real-provider",
        action="store_true",
        help="Use the configured real LLM provider instead of the deterministic mock.",
    )
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text())
    result = run_generation_demo(
        fixture=fixture,
        workspace=args.workspace,
        no_visual_assets=args.no_visual_assets,
        use_real_provider=args.real_provider,
    )
    print(result["output"])


if __name__ == "__main__":
    main()
