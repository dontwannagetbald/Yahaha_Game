"""Create the payload that the backend can persist as a new revision job."""

from __future__ import annotations

import copy

from agent.revision_graph.nodes._helpers import append_log, merged_game_plan
from agent.revision_graph.state import RevisionState


def create_revision_job_payload(state: RevisionState) -> dict:
    revised_game_plan = merged_game_plan(state.base_game_plan, state.game_plan_patch)
    payload = {
        "parent_job_id": state.parent_job.get("id"),
        "create_session_id": state.parent_job.get("create_session_id"),
        "revision_intent": state.revision_intent,
        "game_plan": revised_game_plan,
        "material_usage": copy.deepcopy(state.base_material_usage),
        "generated_result": copy.deepcopy(state.generated_result),
    }

    return {
        "revision_status": "ready_to_generate",
        "requires_regeneration": True,
        "revision_job_payload": payload,
        "assistant_response": {
            "message": "我会按这个修改创建一个新版本，不会覆盖上一版产物。",
            "suggestions": [],
            "actions": ["create_revision_job"],
        },
        "agent_logs": append_log(state, "create_revision_job_payload", "已创建 revision job payload"),
    }
