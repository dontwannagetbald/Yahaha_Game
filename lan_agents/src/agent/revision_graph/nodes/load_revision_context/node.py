"""Load and validate immutable context for a post-generation revision."""

from __future__ import annotations

from agent.revision_graph.nodes._helpers import append_log
from agent.revision_graph.state import RevisionState


def load_revision_context(state: RevisionState) -> dict:
    if state.parent_job.get("status") not in {"succeeded", "failed"}:
        return {
            "revision_status": "needs_clarification",
            "requires_regeneration": False,
            "error_message": "只能基于 succeeded 或 failed 的生成任务创建修改版本。",
            "assistant_response": {
                "message": "这个任务还不能修改，请等当前生成结束后再试。",
                "suggestions": [],
                "actions": [],
            },
            "agent_logs": append_log(state, "load_revision_context", "父任务状态不允许 revision", "warning"),
        }

    return {
        "revision_status": "understanding",
        "agent_logs": append_log(state, "load_revision_context", "已加载上一版任务和产物上下文"),
    }
