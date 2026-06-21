"""Route the current conversation event."""

from __future__ import annotations

from agent.conversation_graph.events import VALID_EVENT_TYPES
from agent.state import ConversationState


def route_user_event(state: ConversationState) -> str:
    """Return the branch name for the current user event."""
    if state.conversation_status == "error":
        return "invalid"
    event_type = state.user_event.get("type")
    if event_type in VALID_EVENT_TYPES:
        return str(event_type)
    return "invalid"
