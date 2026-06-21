"""Local demo for stage-B Orchestrator contract generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent.generation_graph.orchestrator.planner import OrchestratorPlanner
from agent.generation_graph.state import GenerationState


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the stage-B Orchestrator demo")
    parser.add_argument("--fixture", required=True, help="Path to confirmed session fixture")
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text())
    result = OrchestratorPlanner().plan(GenerationState(**fixture))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
