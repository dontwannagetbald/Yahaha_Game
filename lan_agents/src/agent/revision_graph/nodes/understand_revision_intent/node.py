"""Classify whether the user's post-generation revision request is actionable."""

from __future__ import annotations

from agent.revision_graph.nodes._helpers import append_log
from agent.revision_graph.state import RevisionState


def understand_revision_intent(state: RevisionState) -> dict:
    if state.revision_status == "needs_clarification":
        return {}

    from agent.revision_graph.services import revision_planner

    update = revision_planner.RevisionPlanner().plan(state)
    if update.get("revision_status") == "clear":
        log_message = "已通过 RevisionPlanner 识别明确修改意图"
        level = "info"
    else:
        log_message = "RevisionPlanner 需要追问修改意图"
        level = "warning"
    update["agent_logs"] = append_log(state, "understand_revision_intent", log_message, level)
    return update
