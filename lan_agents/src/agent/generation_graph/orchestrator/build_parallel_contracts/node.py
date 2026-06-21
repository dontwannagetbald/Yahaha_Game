"""Node that builds aligned development and asset contracts."""

from __future__ import annotations

from typing import Any

from agent.generation_graph.orchestrator.planner import OrchestratorPlanner
from agent.generation_graph.state import GenerationState
from agent.providers import LLMProvider


def build_parallel_contracts(
    state: GenerationState, provider: LLMProvider | None = None
) -> dict[str, Any]:
    """Return Orchestrator-generated parallel execution contracts."""
    return OrchestratorPlanner(provider=provider).plan(state)
