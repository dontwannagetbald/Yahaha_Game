"""Return a clarification response without creating a revision job."""

from __future__ import annotations

from agent.revision_graph.nodes._helpers import append_log
from agent.revision_graph.state import RevisionState


def ask_clarifying_question(state: RevisionState) -> dict:
    message = state.error_message or "你想主要改哪一块？可以说角色、背景、难度、玩法目标或操作方式。"
    return {
        "revision_status": "needs_clarification",
        "requires_regeneration": False,
        "game_plan_patch": {},
        "revision_job_payload": {},
        "assistant_response": {
            "message": message,
            "suggestions": ["降低难度", "更换主角", "修改背景"],
            "actions": [],
        },
        "agent_logs": append_log(state, "ask_clarifying_question", "已返回澄清问题"),
    }
