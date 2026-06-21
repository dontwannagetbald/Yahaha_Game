"""State schema for the first-stage conversation graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def default_user_requirements() -> dict[str, Any]:
    """Return the empty accumulated user requirements object."""
    return {
        "intent_summary": "",
        "must_have": [],
        "nice_to_have": [],
        "constraints": [],
        "open_questions": [],
        "answered_questions": [],
        "preference_profile": {
            "genre_candidates": [],
            "visual_style": None,
            "tone": None,
            "target_session_length": None,
            "difficulty": None,
        },
        "revision_count": 0,
    }


def default_game_plan() -> dict[str, Any]:
    """Return the empty game plan object used before planning starts."""
    return {
        "plan_id": None,
        "title": "",
        "introduction": "",
        "tags": [],
        "gameplay": "",
        "core_loop": [],
        "style": "",
        "characters": [],
        "win_condition": "",
        "lose_condition": "",
        "controls": "",
        "suggestions": [],
        "confidence": "low",
    }


def default_material_usage() -> dict[str, Any]:
    """Return the first-stage material usage object."""
    return {"assets": []}


def default_assistant_response() -> dict[str, Any]:
    """Return the empty response projected back to the Create UI."""
    return {
        "message": "",
        "suggestions": [],
        "card": None,
        "actions": [],
    }


def default_conversation_history() -> list[dict[str, Any]]:
    """Return the recent user-visible conversation history for LLM context."""
    return []


@dataclass
class ConversationState:
    """First-stage conversation state shared by all conversation graph nodes."""

    user_requirements: dict[str, Any] = field(default_factory=default_user_requirements)
    game_plan: dict[str, Any] = field(default_factory=default_game_plan)
    material_usage: dict[str, Any] = field(default_factory=default_material_usage)
    user_event: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=default_conversation_history)
    assistant_response: dict[str, Any] = field(default_factory=default_assistant_response)
    handoff_to_generation: bool = False
    conversation_status: str = "collecting"
