"""Local demo for stage-B Coding Agent draft generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent.generation_graph.coding_agent.draft_code.node import draft_code
from agent.generation_graph.orchestrator.planner import deterministic_contracts
from agent.generation_graph.state import GenerationState
from agent.providers import MockLLMProvider, ProviderConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the stage-B Coding Agent demo")
    parser.add_argument("--fixture", required=True, help="Path to coding fixture JSON")
    parser.add_argument(
        "--workspace",
        default="output/coding-demo",
        help="Artifact workspace for generated bundle files",
    )
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text())
    state = GenerationState(**fixture)
    if not state.development_brief:
        contracts = deterministic_contracts(state)
        state.development_brief = contracts["development_brief"]
        state.asset_manifest_plan = contracts["asset_manifest_plan"]
        state.game_spec = contracts["game_spec"]
    state.artifact_workspace = args.workspace

    provider = None
    if ProviderConfig.from_env().provider.lower() == "mock":
        provider = MockLLMProvider(
            response={
                "index_html": "<!doctype html><html><head><meta charset='utf-8'><link rel='stylesheet' href='style.css'></head><body><canvas id='game' width='960' height='540'></canvas><script src='game.js'></script></body></html>",
                "style_css": "html, body { margin: 0; background: #101418; color: #fff; } canvas { display: block; margin: 0 auto; }",
                "game_js": "const player = 'assets/player.png'; const canvas = document.getElementById('game'); const ctx = canvas.getContext('2d'); ctx.fillStyle = '#101418'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.fillStyle = '#ffc200'; ctx.fillText('Yahaha Coding Agent Demo', 24, 40); console.log(player);",
                "coding_notes": [
                    "Mock provider emitted a deterministic demo bundle.",
                    "Real provider should replace this with gameplay-specific code.",
                ],
            }
        )

    result = draft_code(state, provider=provider)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
