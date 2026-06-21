"""Merge chat messages into accumulated requirements."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.nodes._helpers import (
    append_unique,
    copy_dict,
    extract_constraints,
    extract_must_haves,
    extract_nice_to_haves,
    merge_preference_profile,
    merge_summary,
    next_open_questions,
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
    requirements["must_have"] = append_unique(
        requirements.get("must_have", []), extract_must_haves(message)
    )
    requirements["nice_to_have"] = append_unique(
        requirements.get("nice_to_have", []), extract_nice_to_haves(message)
    )
    requirements["constraints"] = append_unique(
        requirements.get("constraints", []), extract_constraints(message)
    )
    requirements["preference_profile"] = merge_preference_profile(
        requirements.get("preference_profile", {}), message
    )
    requirements["open_questions"] = next_open_questions(requirements)
    requirements["revision_count"] = int(requirements.get("revision_count", 0)) + 1

    update: dict[str, Any] = {"user_requirements": requirements}
    material_update = sync_material_usage_from_message(state.material_usage, message)
    if material_update is not None:
        update["material_usage"] = material_update
    return update
