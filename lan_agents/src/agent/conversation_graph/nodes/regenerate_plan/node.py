"""Refresh the visible plan while keeping requirements."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.services.regenerate_planner import RegeneratePlanner
from agent.state import ConversationState


def regenerate_plan(state: ConversationState) -> dict[str, Any]:
    """Refresh the visible plan while keeping requirements and material usage."""
    return RegeneratePlanner().regenerate(state)
