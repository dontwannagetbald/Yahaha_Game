"""Classify whether the user's post-generation revision request is actionable."""

from __future__ import annotations

from agent.revision_graph.nodes._helpers import append_log, build_patch_from_message, is_unclear_revision, summarize_intent
from agent.revision_graph.state import RevisionState


def understand_revision_intent(state: RevisionState) -> dict:
    if state.revision_status == "needs_clarification":
        return {}

    if is_unclear_revision(state.user_message):
        return {
            "revision_status": "needs_clarification",
            "requires_regeneration": False,
            "agent_logs": append_log(state, "understand_revision_intent", "修改意图不够明确", "warning"),
        }

    patch = build_patch_from_message(state.user_message)
    if not patch:
        return {
            "revision_status": "needs_clarification",
            "requires_regeneration": False,
            "agent_logs": append_log(state, "understand_revision_intent", "未能形成稳定修改补丁", "warning"),
        }

    return {
        "revision_status": "clear",
        "revision_intent": summarize_intent(state.user_message, patch),
        "game_plan_patch": patch,
        "requires_regeneration": True,
        "agent_logs": append_log(state, "understand_revision_intent", "已识别明确修改意图"),
    }
