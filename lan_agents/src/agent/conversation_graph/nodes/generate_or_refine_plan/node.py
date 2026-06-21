"""Generate or refine game_plan through DesignPlanner."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.services.design_planner import DesignPlanner
from agent.state import ConversationState


def generate_or_refine_plan(state: ConversationState) -> dict[str, Any]:
    """Create a plan update from accumulated requirements."""
    return DesignPlanner().plan(state)
