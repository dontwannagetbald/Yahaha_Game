"""Finalize a bounded patch for the previous game plan."""

from __future__ import annotations

from agent.revision_graph.nodes._helpers import append_log
from agent.revision_graph.state import RevisionState


def build_revision_patch(state: RevisionState) -> dict:
    return {
        "revision_status": "patch_built",
        "agent_logs": append_log(state, "build_revision_patch", "已生成 game_plan patch"),
    }
