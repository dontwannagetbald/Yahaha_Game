"""Lock the current plan for generation."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.nodes._helpers import (
    assets_missing_usage,
    followup_for_missing_fields,
    missing_game_plan_fields,
)
from agent.state import ConversationState, default_assistant_response


def lock_confirmation(state: ConversationState) -> dict[str, Any]:
    """Lock the current plan for generation."""
    missing_fields = missing_game_plan_fields(state.game_plan)
    missing_assets = assets_missing_usage(state.material_usage)
    if missing_fields:
        followup = followup_for_missing_fields(missing_fields)
        return {
            "handoff_to_generation": False,
            "conversation_status": "collecting",
            "assistant_response": {
                "message": f"还不能开始生成。{followup['message']}",
                "suggestions": followup["suggestions"],
                "card": None,
                "actions": [],
            },
        }
    if missing_assets:
        return {
            "handoff_to_generation": False,
            "conversation_status": "collecting",
            "assistant_response": {
                "message": "还有素材没有明确用途，请先告诉我这些素材要怎么用。",
                "suggestions": ["作为主角", "作为背景", "作为音效"],
                "card": None,
                "actions": [],
            },
        }
    return {
        "assistant_response": state.assistant_response or default_assistant_response(),
        "handoff_to_generation": True,
        "conversation_status": "confirmed",
    }
