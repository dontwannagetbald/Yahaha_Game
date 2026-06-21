"""Merge chat messages into accumulated requirements."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.nodes._helpers import (
    append_unique,
    copy_dict,
    extract_constraints,
    merge_summary,
    sync_material_usage_from_message,
)
from agent.state import ConversationState


def update_requirements(state: ConversationState) -> dict[str, Any]:
    """Merge the latest chat message into accumulated requirements."""
    message = str(state.user_event.get("message", "")).strip()
    requirements = copy_dict(state.user_requirements)
    if not message:
        return {"user_requirements": requirements}

    requirements["intent_summary"] = merge_summary(
        requirements.get("intent_summary", ""), message
    )
    requirements["constraints"] = append_unique(
        requirements.get("constraints", []), extract_constraints(message)
    )
    requirements["revision_count"] = int(requirements.get("revision_count", 0)) + 1

    update: dict[str, Any] = {"user_requirements": requirements}
    material_update = sync_material_usage_from_message(state.material_usage, message)
    if material_update is not None:
        update["material_usage"] = material_update
    return update
