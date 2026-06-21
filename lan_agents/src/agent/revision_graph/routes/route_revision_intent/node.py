"""Route clear and unclear post-generation revision requests."""

from __future__ import annotations

from agent.revision_graph.state import RevisionState


def route_revision_intent(state: RevisionState) -> str:
    if state.revision_status == "clear":
        return "clear"
    return "unclear"
