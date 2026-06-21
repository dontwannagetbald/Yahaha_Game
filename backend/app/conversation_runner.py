from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Protocol

from app.config import settings


class ConversationGraph(Protocol):
    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
        ...


_conversation_graph: ConversationGraph | None = None


def get_conversation_graph() -> ConversationGraph:
    """Return the configured LangGraph conversation graph."""
    global _conversation_graph
    if _conversation_graph is None:
        _ensure_lan_agents_on_path()
        from agent.graph import conversation_graph

        _conversation_graph = conversation_graph
    return _conversation_graph


async def run_conversation_graph(state: dict[str, Any]) -> dict[str, Any]:
    """Invoke the real first-stage conversation graph and normalize the output."""
    result = await get_conversation_graph().ainvoke(state)
    return normalize_conversation_state(result)


def normalize_conversation_state(state: dict[str, Any]) -> dict[str, Any]:
    """Keep only the state fields persisted by the backend Create Session."""
    game_plan = state.get("game_plan") or {}
    assistant_response = state.get("assistant_response") or {}
    card = assistant_response.get("card")
    if card is None and _has_card_fields(game_plan):
        card = {
            "plan_id": game_plan.get("plan_id"),
            "title": game_plan.get("title"),
            "introduction": game_plan.get("introduction"),
            "tags": game_plan.get("tags"),
        }
    if card is not None:
        card = {
            "plan_id": card.get("plan_id"),
            "title": card.get("title"),
            "introduction": card.get("introduction"),
            "tags": card.get("tags") or [],
        }

    return {
        "conversation_status": state.get("conversation_status") or "collecting",
        "user_requirements": state.get("user_requirements") or {},
        "game_plan": game_plan,
        "material_usage": _normalize_material_usage(state.get("material_usage")),
        "assistant_response": {
            "message": str(assistant_response.get("message") or ""),
            "suggestions": [
                str(suggestion)
                for suggestion in assistant_response.get("suggestions", [])
                if isinstance(suggestion, str)
            ],
            "card": card,
            "actions": [
                str(action)
                for action in assistant_response.get("actions", [])
                if isinstance(action, str)
            ],
        },
        "handoff_to_generation": bool(state.get("handoff_to_generation", False)),
    }


def _normalize_material_usage(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"assets": []}
    assets = value.get("assets")
    if not isinstance(assets, list):
        assets = []
    return {"assets": assets}


def _has_card_fields(game_plan: dict[str, Any]) -> bool:
    return all(
        game_plan.get(field)
        for field in ("plan_id", "title", "introduction", "tags")
    )


def _ensure_lan_agents_on_path() -> None:
    src_path = Path(settings.lan_agents_src_path)
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
