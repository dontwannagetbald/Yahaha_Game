"""Validate and normalize the current user event."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.events import VALID_EVENT_TYPES
from agent.conversation_graph.nodes._helpers import state_defaults_update
from agent.state import ConversationState


def ingest_user_event(state: ConversationState) -> dict[str, Any]:
    """Validate the current user event before routing."""
    base_update = state_defaults_update(state)
    event_type = state.user_event.get("type")
    if event_type not in VALID_EVENT_TYPES:
        return {
            **base_update,
            "conversation_status": "error",
            "assistant_response": {
                "message": "我没有理解这次操作，请重新发送消息或点击可用按钮。",
                "suggestions": ["重新输入想法", "上传素材", "换一换"],
                "card": None,
                "actions": [],
            },
        }
    if event_type == "chat" and not str(state.user_event.get("message", "")).strip():
        return {
            **base_update,
            "conversation_status": "error",
            "assistant_response": {
                "message": "请先告诉我你想做什么游戏。",
                "suggestions": ["做一个躲避障碍游戏", "做一个收集星星游戏"],
                "card": None,
                "actions": [],
            },
        }
    return {**base_update, "conversation_status": "collecting"}
