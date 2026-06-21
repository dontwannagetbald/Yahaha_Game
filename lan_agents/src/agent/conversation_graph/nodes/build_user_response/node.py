"""Build the response shape consumed by the Create UI."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.nodes._helpers import (
    card_from_game_plan,
    followup_for_missing_fields,
    missing_confirmable_game_plan_fields,
)
from agent.conversation_graph.services.tone import (
    friendly_design_message,
    friendly_ready_message,
)
from agent.state import ConversationState


def build_user_response(state: ConversationState) -> dict[str, Any]:
    """Build the response shape consumed by the Create UI."""
    missing_fields = missing_confirmable_game_plan_fields(state.game_plan)
    card = card_from_game_plan(state.game_plan)
    if state.user_event.get("type") == "upload_assets":
        return {
            "conversation_status": "collecting" if missing_fields else "ready_to_confirm",
            "assistant_response": {
                "message": "",
                "suggestions": [],
                "card": None if missing_fields else card,
                "actions": [] if missing_fields or not card else ["generate", "regenerate"],
            },
        }
    if missing_fields:
        followup = followup_for_missing_fields(missing_fields)
        if state.assistant_response.get("message") or state.assistant_response.get(
            "suggestions"
        ):
            message = state.assistant_response.get("message", "")
            suggestions = state.assistant_response.get("suggestions", [])
            return {
                "conversation_status": "collecting",
                "assistant_response": {
                    "message": friendly_design_message(
                        message,
                        missing_fields=missing_fields,
                        game_plan=state.game_plan,
                    ),
                    "suggestions": suggestions,
                    "card": None,
                    "actions": [],
                },
            }
        return {
            "conversation_status": "collecting",
            "assistant_response": {
                "message": friendly_design_message(
                    followup["message"],
                    missing_fields=missing_fields,
                    game_plan=state.game_plan,
                ),
                "suggestions": followup["suggestions"],
                "card": None,
                "actions": [],
            },
        }

    suggestions = state.game_plan.get("suggestions") or []
    return {
        "conversation_status": "ready_to_confirm",
        "assistant_response": {
            "message": friendly_ready_message(),
            "suggestions": suggestions if not card else [],
            "card": card,
            "actions": ["generate", "regenerate"] if card else [],
        }
    }
