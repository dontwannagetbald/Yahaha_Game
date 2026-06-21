"""Build a safe user-facing error response."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.nodes._helpers import safe_text, string_suggestions
from agent.state import ConversationState


def build_error_response(state: ConversationState) -> dict[str, Any]:
    """Build a safe, user-facing error response."""
    response = state.assistant_response or {}
    fallback_message = "这次输入暂时不能处理，请换一种方式再试。"
    return {
        "conversation_status": "error",
        "assistant_response": {
            "message": safe_text(response.get("message"), fallback_message),
            "suggestions": string_suggestions(
                response.get("suggestions"), ["重新输入想法", "上传素材"]
            ),
            "card": None,
            "actions": [],
        },
    }
